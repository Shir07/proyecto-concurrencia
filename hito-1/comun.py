"""
Núcleo compartido del Hito 1 — Concurrencia en CPU.

Contiene los componentes y funciones compartidas de la versión secuencial, las paralelas y el
benchmark: cómo se construye el vector, cómo se suma un bloque, cómo se
cronometra y las fórmulas de Amdahl y Karp-Flatt.

Problema elegido: suma de un vector grande de float32.
Es el mismo *shape* que usan las Clases 2 y 4 y el Hito 2 (kernels CUDA),
así que el trabajo hecho acá se reusará después.
"""

from __future__ import annotations

import os
import statistics
import time
from typing import Callable, Sequence

import numpy as np

# Tamaños de problema

N_POR_DEFECTO = 16_777_216

# El backend "puro" (bucle de Python, sin NumPy) es ~100x más lento, así que
# corre con un N reducido. El N usado queda registrado en el CSV 
N_PURO_POR_DEFECTO = 2_000_000


# Datos

def crear_vector(n: int, semilla: int | None = None) -> np.ndarray:
    """Devuelve el vector de entrada como float32.

    Con `semilla=None` devuelve un vector de unos: la suma esperada es
    exactamente N

    Con una semilla devuelve valores aleatorios en [0, 1), útil para
    comprobar que el resultado no depende de que todos los elementos sean
    iguales.
    """
    if semilla is None:
        return np.ones(n, dtype=np.float32)
    rng = np.random.default_rng(semilla)
    return rng.random(n, dtype=np.float32)


def suma_esperada(a: np.ndarray) -> float:
    """Valor de referencia calculado en float64 de una sola pasada."""
    return float(a.sum(dtype=np.float64))


# Suma de un bloque: los dos backends
def suma_bloque_numpy(a: np.ndarray, ini: int, fin: int) -> float:
    """Suma a[ini:fin] con NumPy.

    El acumulador es float64 aunque el vector sea float32: sumar 16 millones
    de valores en float32 pierde precisión (a partir de 2**24 el "+1" se
    redondea y la suma se estanca). Esto hay que mencionarlo en el informe.
    """
    return float(a[ini:fin].sum(dtype=np.float64))


def suma_bloque_puro(a: np.ndarray, ini: int, fin: int) -> float:
    """Suma a[ini:fin] con un bucle de Python, sin NumPy.

    Cada iteración ejecuta bytecode de CPython, así que el GIL está tomado
    todo el tiempo. Versión orientada a demostrar que "más hilos" no
    implica "más rápido" en CPython.
    """
    total = 0.0
    for x in a[ini:fin]:
        total += float(x)
    return total


BACKENDS: dict[str, Callable[[np.ndarray, int, int], float]] = {
    "numpy": suma_bloque_numpy,
    "puro": suma_bloque_puro,
}


def n_por_defecto(backend: str) -> int:
    return N_PURO_POR_DEFECTO if backend == "puro" else N_POR_DEFECTO


def tam_bloque_por_defecto(n: int, hilos: int) -> int:
    """Bloques chicos = mejor balanceo de carga, más contención en el lock.

    Apuntamos a ~8 bloques por hilo: suficiente para que un hilo que termina
    antes agarre más trabajo, sin que el despacho domine el tiempo.
    """
    return max(1024, n // max(1, hilos * 8))


# ---------------------------------------------------------------------------
# Medición
# ---------------------------------------------------------------------------
def cronometrar(fn: Callable[[], float], repeticiones: int = 5):
    """Corre `fn` varias veces y devuelve (resultado, mediana, tiempos).

    El enunciado pide mediana de al menos 3 corridas y declarar cuál se usó.
    Devolvemos todos los tiempos para poder reportar también min/max.
    """
    tiempos: list[float] = []
    resultado = 0.0
    for _ in range(repeticiones):
        t0 = time.perf_counter()
        resultado = fn()
        t1 = time.perf_counter()
        tiempos.append(t1 - t0)
    return resultado, statistics.median(tiempos), tiempos


def es_correcta(obtenida: float, esperada: float, tol_rel: float = 1e-9) -> bool:
    """Compara con tolerancia relativa (aritmética de punto flotante)."""
    if esperada == 0.0:
        return abs(obtenida) <= tol_rel
    return abs(obtenida - esperada) / abs(esperada) <= tol_rel


# ---------------------------------------------------------------------------
# Teoría: Amdahl y Karp-Flatt
# ---------------------------------------------------------------------------
def amdahl(s: float, t: int) -> float:
    """Aceleración teórica máxima con fracción secuencial `s` y `t` hilos.

        S(T) = 1 / (s + (1 - s) / T)

    Con T -> infinito el techo es 1/s. Ese techo es lo que hay que contrastar
    contra la curva medida.
    """
    return 1.0 / (s + (1.0 - s) / t)


def karp_flatt(speedup: float, t: int) -> float:
    """Fracción secuencial *experimental* (métrica de Karp-Flatt).

        e = (1/S(T) - 1/T) / (1 - 1/T)

    En vez de inventar un `s`, lo despejamos de las mediciones. Si `e` crece
    con T, la pérdida no es sólo la fracción secuencial: hay sobrecarga de
    paralelización (creación de hilos, contención del lock, ancho de banda
    de memoria). 
    """
    if t <= 1 or speedup <= 0:
        return float("nan")
    return (1.0 / speedup - 1.0 / t) / (1.0 - 1.0 / t)


# ---------------------------------------------------------------------------
# Entorno
# ---------------------------------------------------------------------------
def hilos_disponibles() -> int:
    return os.cpu_count() or 1


def lista_de_hilos(maximo: int | None = None) -> list[int]:
    """Potencias de 2 hasta 2x los núcleos, para ver la sobre-suscripción."""
    tope = (maximo or hilos_disponibles()) * 2
    hilos, t = [], 1
    while t <= tope:
        hilos.append(t)
        t *= 2
    if hilos_disponibles() not in hilos:
        hilos.append(hilos_disponibles())
    return sorted(set(hilos))


def describir_entorno() -> dict[str, str]:
    import platform

    return {
        "python": platform.python_version(),
        "implementacion": platform.python_implementation(),
        "sistema": f"{platform.system()} {platform.release()}",
        "maquina": platform.machine(),
        "procesador": platform.processor() or "(desconocido)",
        "cpu_count": str(hilos_disponibles()),
        "numpy": np.__version__,
    }


def imprimir_entorno() -> None:
    print("--- entorno ---")
    for k, v in describir_entorno().items():
        print(f"{k:16s} {v}")
    print("---------------")


def tabla(filas: Sequence[Sequence[object]], encabezados: Sequence[str]) -> str:
    """Tabla de texto simple para pegar en el informe."""
    cols = [list(map(str, col)) for col in zip(encabezados, *filas)] if filas else []
    anchos = [max(len(c) for c in col) for col in cols]
    sep = "  ".join("-" * a for a in anchos)
    lineas = ["  ".join(h.ljust(a) for h, a in zip(encabezados, anchos)), sep]
    for fila in filas:
        lineas.append("  ".join(str(c).ljust(a) for c, a in zip(fila, anchos)))
    return "\n".join(lineas)
