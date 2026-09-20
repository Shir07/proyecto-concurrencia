"""
Versión PARALELA con hilos (threading).

Estructura (la misma que el esqueleto en C++ del repo de la materia):

  - una COLA DINÁMICA de bloques, protegida por un `threading.Lock`
  - N hilos trabajadores que piden bloques hasta que no queda ninguno
  - un ACUMULADOR compartido, también protegido por un `threading.Lock`

Los dos usos del lock son los dos casos de manual de la Clase 3:
exclusión mutua sobre un índice compartido y sobre un acumulador compartido.

Por qué cola dinámica y no un reparto fijo: si un hilo se frena (el SO lo
desaloja, otro proceso compite por el núcleo), con reparto fijo el resto
espera. Con cola dinámica los demás siguen agarrando trabajo. Es balanceo
de carga, y se nota sobre todo con sobre-suscripción (más hilos que núcleos).

Uso:
    python paralelo.py 16777216 4
    python paralelo.py 2000000 4 --backend puro
    python paralelo.py 16777216 4 --lock-por-bloque   # experimento de contención
"""

from __future__ import annotations

import argparse
import threading

import comun


class ColaDeBloques:
    """Reparte rangos [ini, fin) a demanda. Thread-safe."""

    def __init__(self, n: int, tam_bloque: int) -> None:
        self._n = n
        self._tam = tam_bloque
        self._siguiente = 0               # <- estado compartido
        self._lock = threading.Lock()     # <- primitiva de sincronización
        self.bloques_entregados = 0

    def proximo(self) -> tuple[int, int] | None:
        """Devuelve el siguiente bloque, o None si ya no queda trabajo.

        La sección crítica es mínima a propósito: sólo leer y avanzar el
        índice. La suma del bloque ocurre FUERA del lock; si estuviera
        adentro, el programa sería secuencial con pasos extra.
        """
        with self._lock:
            ini = self._siguiente
            if ini >= self._n:
                return None
            fin = min(ini + self._tam, self._n)
            self._siguiente = fin
            self.bloques_entregados += 1
            return ini, fin


class Acumulador:
    """Suma global protegida por lock."""

    def __init__(self) -> None:
        self._total = 0.0
        self._lock = threading.Lock()

    def sumar(self, valor: float) -> None:
        with self._lock:
            self._total += valor

    @property
    def total(self) -> float:
        with self._lock:
            return self._total


def _trabajador(cola: ColaDeBloques, acum: Acumulador, a, backend: str,
                lock_por_bloque: bool) -> None:
    sumar = comun.BACKENDS[backend]
    parcial = 0.0
    while True:
        bloque = cola.proximo()
        if bloque is None:
            break
        ini, fin = bloque
        valor = sumar(a, ini, fin)
        if lock_por_bloque:
            # Variante "alternativa": toma el lock una vez por bloque.
            # Sirve para medir contención nuestro informe.
            acum.sumar(valor)
        else:
            # Variante por defecto: acumular local y tomar el lock UNA sola
            # vez al final. Reducción privada + una escritura global.
            parcial += valor
    if not lock_por_bloque:
        acum.sumar(parcial)


def suma_paralela(a, hilos: int, tam_bloque: int, backend: str = "numpy",
                  lock_por_bloque: bool = False) -> float:
    n = a.shape[0]
    cola = ColaDeBloques(n, tam_bloque)
    acum = Acumulador()

    trabajadores = [
        threading.Thread(
            target=_trabajador,
            args=(cola, acum, a, backend, lock_por_bloque),
            name=f"trabajador-{i}",
        )
        for i in range(hilos)
    ]
    for t in trabajadores:
        t.start()
    for t in trabajadores:
        t.join()   # sin el join, el total se lee antes de tiempo

    return acum.total


def main() -> None:
    p = argparse.ArgumentParser(description="Suma paralela con hilos + lock")
    p.add_argument("n", nargs="?", type=int, default=None)
    p.add_argument("hilos", nargs="?", type=int, default=None)
    p.add_argument("--backend", choices=list(comun.BACKENDS), default="numpy")
    p.add_argument("--tam-bloque", type=int, default=None)
    p.add_argument("--repeticiones", type=int, default=3)
    p.add_argument("--semilla", type=int, default=None)
    p.add_argument("--lock-por-bloque", action="store_true",
                   help="toma el lock global una vez por bloque (más contención)")
    args = p.parse_args()

    n = args.n or comun.n_por_defecto(args.backend)
    hilos = args.hilos or comun.hilos_disponibles()
    tam_bloque = args.tam_bloque or comun.tam_bloque_por_defecto(n, hilos)

    a = comun.crear_vector(n, args.semilla)
    esperada = comun.suma_esperada(a)

    resultado, mediana, tiempos = comun.cronometrar(
        lambda: suma_paralela(a, hilos, tam_bloque, args.backend, args.lock_por_bloque),
        args.repeticiones,
    )

    ok = comun.es_correcta(resultado, esperada)
    print(f"n={n}  hilos={hilos}  backend={args.backend}  tam_bloque={tam_bloque}  "
          f"lock_por_bloque={args.lock_por_bloque}")
    print(f"suma={resultado:.6f}  esperada={esperada:.6f}  ok={ok}")
    print(f"t_mediana={mediana:.6f} s  (corridas={args.repeticiones}, "
          f"min={min(tiempos):.6f}, max={max(tiempos):.6f})")


if __name__ == "__main__":
    main()
