"""
Versión SECUENCIAL — referencia completa.

Es el T_seq contra el que se mide todo. Un solo hilo, mismo algoritmo y mismo
backend que la versión paralela: recorre el vector en bloques y acumula.

Uso:
    python secuencial.py 16777216
    python secuencial.py 2000000 --backend puro
"""

from __future__ import annotations

import argparse

import comun


def suma_secuencial(a, tam_bloque: int, backend: str = "numpy") -> float:
    """Recorre el vector bloque por bloque, en un solo hilo.

    Podría ser simplemente `a.sum()`, pero se hace por bloques a propósito:
    así la versión paralela ejecuta EXACTAMENTE el mismo trabajo y la
    comparación es honesta (mismo tamaño de bloque, mismo orden de reducción,
    misma cantidad de llamadas).
    """
    sumar = comun.BACKENDS[backend]
    total = 0.0
    n = a.shape[0]
    ini = 0
    while ini < n:
        fin = min(ini + tam_bloque, n)
        total += sumar(a, ini, fin)
        ini = fin
    return total


def main() -> None:
    p = argparse.ArgumentParser(description="Suma secuencial de un vector de float32")
    p.add_argument("n", nargs="?", type=int, default=None, help="tamaño del vector")
    p.add_argument("--backend", choices=list(comun.BACKENDS), default="numpy")
    p.add_argument("--tam-bloque", type=int, default=None)
    p.add_argument("--repeticiones", type=int, default=3)
    p.add_argument("--semilla", type=int, default=None,
                   help="si se omite, el vector es todo unos y la suma esperada es N")
    args = p.parse_args()

    n = args.n or comun.n_por_defecto(args.backend)
    tam_bloque = args.tam_bloque or comun.tam_bloque_por_defecto(n, 1)

    a = comun.crear_vector(n, args.semilla)
    esperada = comun.suma_esperada(a)

    resultado, mediana, tiempos = comun.cronometrar(
        lambda: suma_secuencial(a, tam_bloque, args.backend), args.repeticiones
    )

    ok = comun.es_correcta(resultado, esperada)
    print(f"n={n}  backend={args.backend}  tam_bloque={tam_bloque}")
    print(f"suma={resultado:.6f}  esperada={esperada:.6f}  ok={ok}")
    print(f"t_mediana={mediana:.6f} s  (corridas={args.repeticiones}, "
          f"min={min(tiempos):.6f}, max={max(tiempos):.6f})")


if __name__ == "__main__":
    main()
