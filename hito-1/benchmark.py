"""
BENCHMARK — mide secuencial vs. paralelo variando la cantidad de hilos.

Barre cuatro combinaciones y para cada una calcula S(T) = T_seq / T(T):

  backend  x  ejecución       qué demuestra
  --------------------------------------------------------------------
  puro        hilos           el GIL: S(T) ~ 1 por más hilos que pongas
  puro        procesos        sin GIL: S(T) se acerca a la recta ideal
  numpy       hilos           NumPy libera el GIL -> los hilos SÍ sirven
  numpy       procesos        igual, pero pagando el arranque de procesos

Cada combinación tiene su propia referencia secuencial (mismo backend, mismo
tamaño de bloque, un solo hilo). 

Salidas:
  resultados.csv   una fila por (combinación, T)
  entorno.txt      hardware, versiones y parámetros, para pegar en el informe

Uso:
    python benchmark.py
    python benchmark.py --n 16777216 --n-puro 2000000 --repeticiones 5
    python benchmark.py --combinaciones numpy-hilos puro-hilos
"""

from __future__ import annotations

import argparse
import csv
import multiprocessing as mp
from dataclasses import dataclass, asdict

import numpy as np

import comun
from secuencial import suma_secuencial
from paralelo import suma_paralela
from paralelo_mp import PoolProcesos, medir_arranque, crear_buffer_compartido

COMBINACIONES = ["numpy-hilos", "numpy-procesos", "puro-hilos", "puro-procesos"]


@dataclass
class Fila:
    combinacion: str
    backend: str
    ejecucion: str
    n: int
    tam_bloque: int
    hilos: int
    corridas: int
    t_mediana: float
    t_min: float
    t_max: float
    t_arranque: float          # costo de crear los procesos (0 para hilos)
    speedup: float             # sin contar el arranque
    speedup_con_arranque: float
    eficiencia: float
    karp_flatt: float
    suma: float
    ok: bool


def ajustar_s(puntos: list[tuple[int, float]]) -> float:
    """Ajusta la fracción secuencial `s` de Amdahl a los puntos medidos.
     """
    candidatos = np.linspace(1e-4, 1.0, 10_000)
    mejor_s, mejor_err = 1.0, float("inf")
    for s in candidatos:
        err = sum((comun.amdahl(float(s), t) - medido) ** 2 for t, medido in puntos)
        if err < mejor_err:
            mejor_s, mejor_err = float(s), err
    return mejor_s


def medir_combinacion(combinacion: str, n: int, hilos_lista: list[int],
                      repeticiones: int, semilla: int | None) -> list[Fila]:
    backend, ejecucion = combinacion.split("-")

    # Tamaño de bloque FIJO para toda la combinación: si cambiara con T,
    # estaríamos midiendo dos cosas a la vez.
    tam_bloque = comun.tam_bloque_por_defecto(n, max(hilos_lista))

    if ejecucion == "procesos":
        buffer, a = crear_buffer_compartido(n, semilla)
    else:
        a = comun.crear_vector(n, semilla)
        buffer = None

    esperada = comun.suma_esperada(a)

    print(f"\n### {combinacion}   n={n}  tam_bloque={tam_bloque}  "
          f"corridas={repeticiones}")

    # --- referencia secuencial ---
    _, t_seq, tiempos_seq = comun.cronometrar(
        lambda: suma_secuencial(a, tam_bloque, backend), repeticiones
    )
    print(f"  T_seq = {t_seq:.6f} s")
    if t_seq < 0.05:
        print("  AVISO: T_seq < 50 ms. A esta escala el ruido del sistema y el "
              "arranque de hilos/procesos pesan más que el cálculo.\n"
              "         Subí N (por ejemplo --n 67108864) antes de tomar los "
              "números definitivos del informe.")

    filas: list[Fila] = []
    for t in hilos_lista:
        if ejecucion == "hilos":
            t_arranque = 0.0
            suma, mediana, tiempos = comun.cronometrar(
                lambda t=t: suma_paralela(a, t, tam_bloque, backend), repeticiones
            )
        else:
            # El arranque de los procesos se mide APARTE y no entra en t_mediana:
            # con `spawn` (Windows/macOS) taparía por completo el cálculo.
            t_arranque = medir_arranque(buffer, n, t, backend)
            with PoolProcesos(buffer, n, t, backend) as pool:
                suma, mediana, tiempos = comun.cronometrar(
                    lambda: pool.sumar(tam_bloque), repeticiones
                )

        speedup = t_seq / mediana if mediana > 0 else float("nan")
        s_con_arranque = t_seq / (mediana + t_arranque)
        filas.append(Fila(
            combinacion=combinacion,
            backend=backend,
            ejecucion=ejecucion,
            n=n,
            tam_bloque=tam_bloque,
            hilos=t,
            corridas=repeticiones,
            t_mediana=round(mediana, 6),
            t_min=round(min(tiempos), 6),
            t_max=round(max(tiempos), 6),
            t_arranque=round(t_arranque, 6),
            speedup=round(speedup, 4),
            speedup_con_arranque=round(s_con_arranque, 4),
            eficiencia=round(speedup / t, 4),
            karp_flatt=round(comun.karp_flatt(speedup, t), 4),
            suma=suma,
            ok=comun.es_correcta(suma, esperada),
        ))
        extra = (f"  arranque={t_arranque:.3f}s  S_con_arranque={s_con_arranque:5.3f}"
                 if ejecucion == "procesos" else "")
        print(f"  T={t:>3}  t={mediana:.6f}s  S={speedup:6.3f}  "
              f"E={speedup / t:5.3f}  e_KF={comun.karp_flatt(speedup, t):6.3f}  "
              f"ok={filas[-1].ok}{extra}")

    # También guardamos la corrida secuencial como fila T=0 de referencia
    filas.insert(0, Fila(
        combinacion=combinacion, backend=backend, ejecucion="secuencial",
        n=n, tam_bloque=tam_bloque, hilos=0, corridas=repeticiones,
        t_mediana=round(t_seq, 6), t_min=round(min(tiempos_seq), 6),
        t_max=round(max(tiempos_seq), 6), t_arranque=0.0, speedup=1.0,
        speedup_con_arranque=1.0, eficiencia=1.0,
        karp_flatt=float("nan"), suma=esperada, ok=True,
    ))

    puntos = [(f.hilos, f.speedup) for f in filas if f.hilos > 0]
    s_est = ajustar_s(puntos)
    techo = 1.0 / s_est
    print(f"  s ajustado = {s_est:.4f}  ->  techo de Amdahl = {techo:.2f}x")

    return filas


def main() -> None:
    p = argparse.ArgumentParser(description="Benchmark del Hito 1")
    p.add_argument("--n", type=int, default=comun.N_POR_DEFECTO,
                   help="tamaño del vector para el backend numpy")
    p.add_argument("--n-puro", type=int, default=comun.N_PURO_POR_DEFECTO,
                   help="tamaño del vector para el backend de Python puro")
    p.add_argument("--repeticiones", type=int, default=7,
                   help="corridas por punto; se reporta la mediana")
    p.add_argument("--hilos-max", type=int, default=None)
    p.add_argument("--combinaciones", nargs="+", default=COMBINACIONES,
                   choices=COMBINACIONES)
    p.add_argument("--semilla", type=int, default=None)
    p.add_argument("--salida", default="resultados.csv")
    args = p.parse_args()

    comun.imprimir_entorno()
    hilos_lista = comun.lista_de_hilos(args.hilos_max)
    print(f"barrido de hilos: {hilos_lista}")

    todas: list[Fila] = []
    for combinacion in args.combinaciones:
        n = args.n_puro if combinacion.startswith("puro") else args.n
        todas.extend(medir_combinacion(combinacion, n, hilos_lista,
                                       args.repeticiones, args.semilla))

    with open(args.salida, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(asdict(todas[0]).keys()))
        w.writeheader()
        for fila in todas:
            w.writerow(asdict(fila))

    with open("entorno.txt", "w", encoding="utf-8") as fh:
        for k, v in comun.describir_entorno().items():
            fh.write(f"{k}: {v}\n")
        fh.write(f"metodo_arranque_procesos: {mp.get_start_method()}\n")
        fh.write(f"n_numpy: {args.n}\nn_puro: {args.n_puro}\n")
        fh.write(f"repeticiones: {args.repeticiones}\n")
        fh.write(f"barrido_hilos: {hilos_lista}\n")

    incorrectas = [f for f in todas if not f.ok]
    print(f"\nResultados en {args.salida} y entorno.txt")
    if incorrectas:
        print(f"ATENCIÓN: {len(incorrectas)} corridas dieron una suma incorrecta")
    else:
        print("Todas las sumas coinciden con la referencia.")


if __name__ == "__main__":
    main()