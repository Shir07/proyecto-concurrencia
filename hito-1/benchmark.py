import argparse
import importlib
import os
import statistics
import time

from secuencial import crear_vector, suma_secuencial

GestorSumaParalela = importlib.import_module("paralelo-threading").GestorSumaParalela

BLOQUE = 1 << 16
CANDIDATOS = [1, 2, 4, 8, 16]


def medir(funcion, repeticiones):
    tiempos = []
    resultado = None
    for _ in range(repeticiones):
        inicio = time.perf_counter()
        resultado = funcion()
        fin = time.perf_counter()
        tiempos.append((fin - inicio) * 1000)
    return resultado, statistics.median(tiempos)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("n", type=int, nargs="?", default=1 << 24)
    parser.add_argument("repeticiones", type=int, nargs="?", default=3)
    args = parser.parse_args()

    if args.n < 1:
        raise SystemExit("N >= 1")
    if args.repeticiones < 3:
        raise SystemExit("repeticiones >= 3")

    hw = os.cpu_count() or 0
    vector = crear_vector(args.n)
    esperado = float(args.n)

    suma_seq, ms_seq = medir(lambda: suma_secuencial(vector), args.repeticiones)

    print(f"hardware_concurrency={hw} N={args.n} repeticiones={args.repeticiones}")
    print("hilos,ms,speedup,suma,correcto")
    print(f"seq,{ms_seq:.3f},1.00,{suma_seq},{suma_seq == esperado}")

    for t in CANDIDATOS:
        if hw != 0 and t > hw * 2:
            continue 

        gestor = lambda: GestorSumaParalela(vector, t, BLOQUE).ejecutar()
        suma_par, ms_par = medir(gestor, args.repeticiones)
        speedup = ms_seq / ms_par if ms_par > 0 else 0.0
        print(f"{t},{ms_par:.3f},{speedup:.2f},{suma_par},{suma_par == esperado}")
