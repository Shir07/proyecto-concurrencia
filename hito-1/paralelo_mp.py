"""
Versión PARALELA con procesos (multiprocessing).

Mismo algoritmo que `paralelo.py` — cola dinámica de bloques repartida con un
índice compartido bajo `Lock` — pero ejecutado en procesos en vez de hilos.
Cada proceso tiene su propio intérprete y su propio GIL, así que acá el bucle
de Python puro TAMBIÉN escala.

El vector vive en memoria compartida (`RawArray`): no se copia a cada proceso.
Si se copiara, la serialización dominaría todo y no mediríamos el cálculo.

## Las dos formas de medir, y por qué importan las dos

Crear un proceso es mucho más caro que crear un hilo. En **Windows y macOS** el
método por defecto es `spawn`: cada proceso arranca un intérprete nuevo e
importa este módulo otra vez, lo que cuesta del orden de **cientos de
milisegundos por proceso**. En Linux el default es `fork` y cuesta ~1 ms.

Eso obliga a medir dos cosas por separado.

  **(a) Pool persistente — `PoolProcesos`.** Los procesos se crean UNA vez y
  después reciben trabajo. Sólo se cronometra el cálculo. Es lo que hace
  cualquier programa real (un servidor no levanta procesos por pedido) y es la
  única forma de ver si el algoritmo escala.

  **(b) Arranque incluido — `suma_paralela_procesos`.** Crea los procesos,
  calcula y los destruye, todo adentro del cronómetro. Mide el costo total de
  "paralelizar esto una sola vez".

Si N es chico y como estamos en Windows, (b) puede dar un speedup MENOR A 1: se tarda más que la versión secuencial. Eso no es un error del código, es el resultado
correcto.

Uso:
    python paralelo_mp.py 16777216 4
    python paralelo_mp.py 2000000 4 --backend puro
    python paralelo_mp.py 16777216 4 --incluir-arranque
"""

from __future__ import annotations

import argparse
import multiprocessing as mp
import time
from multiprocessing.sharedctypes import RawArray

import numpy as np

import comun

LISTO = "LISTO"
APAGAR = "APAGAR"


# (a) Pool persistente
def _servidor(buffer, n, backend, cola_cmd, cola_resultados, indice, lock) -> None:
    """Proceso trabajador de vida larga.

    Se queda esperando órdenes en su propia cola. Cuando llega una ronda,
    consume bloques de la cola dinámica compartida hasta agotarla, y devuelve
    su parcial. Después vuelve a esperar.

    Se asigna una cola de comandos individual por trabajador para evitar condiciones de carrera: si todos
    compartieran una, un proceso rápido podría llevarse dos órdenes y dejar a
    otro sin ninguna, colgando la ronda. El reparto de bloques, en cambio, sí
    es compartido y dinámico — ahí está el `Lock`.
    """
    a = np.frombuffer(buffer, dtype=np.float32, count=n)
    sumar = comun.BACKENDS[backend]
    cola_resultados.put(LISTO)

    while True:
        cmd = cola_cmd.get()
        if cmd == APAGAR:
            break
        tam_bloque = cmd
        parcial = 0.0
        while True:
            # --- sección crítica: repartir el próximo bloque ---
            with lock:
                ini = indice.value
                if ini >= n:
                    break
                fin = min(ini + tam_bloque, n)
                indice.value = fin
            # --- fin de la sección crítica ---
            parcial += sumar(a, ini, fin)
        cola_resultados.put(parcial)


class PoolProcesos:
    """Arranca los procesos una vez y después sólo les manda trabajo.

    Se usa como context manager para que se apaguen solos:

        with PoolProcesos(buffer, n, 4, "numpy") as pool:
            total = pool.sumar(tam_bloque)
    """

    def __init__(self, buffer, n: int, procesos: int, backend: str = "numpy") -> None:
        self.n = n
        self.procesos = procesos
        self.indice = mp.Value("q", 0, lock=False)
        self.lock = mp.Lock()
        self.colas_cmd = [mp.Queue() for _ in range(procesos)]
        self.cola_resultados = mp.Queue()

        self.workers = [
            mp.Process(
                target=_servidor,
                args=(buffer, n, backend, self.colas_cmd[i], self.cola_resultados,
                      self.indice, self.lock),
                name=f"proc-{i}",
                daemon=True,
            )
            for i in range(procesos)
        ]
        for w in self.workers:
            w.start()
        # Esperar a que los N intérpretes estén levantados. Sin este
        # handshake, la primera medición incluiría el arranque a escondidas.
        for _ in self.workers:
            assert self.cola_resultados.get() == LISTO

    def sumar(self, tam_bloque: int) -> float:
        self.indice.value = 0
        for cola in self.colas_cmd:
            cola.put(tam_bloque)
        return sum(self.cola_resultados.get() for _ in self.workers)

    def cerrar(self) -> None:
        for cola in self.colas_cmd:
            cola.put(APAGAR)
        for w in self.workers:
            w.join(timeout=5)
            if w.is_alive():
                w.terminate()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.cerrar()
        return False


def medir_arranque(buffer, n: int, procesos: int, backend: str = "numpy") -> float:
    """Cuánto cuesta levantar `procesos` procesos listos para trabajar.

    Este número es el que explica por qué la curva "con arranque" se despega
    de Amdahl. 
    """
    t0 = time.perf_counter()
    pool = PoolProcesos(buffer, n, procesos, backend)
    t1 = time.perf_counter()
    pool.cerrar()
    return t1 - t0



# (b) Arranque incluido en la medición
def _trabajador_efimero(buffer, n, tam_bloque, backend, indice, total, lock) -> None:
    a = np.frombuffer(buffer, dtype=np.float32, count=n)
    sumar = comun.BACKENDS[backend]
    parcial = 0.0
    while True:
        with lock:
            ini = indice.value
            if ini >= n:
                break
            fin = min(ini + tam_bloque, n)
            indice.value = fin
        parcial += sumar(a, ini, fin)
    with lock:
        total.value += parcial


def suma_paralela_procesos(buffer, n: int, procesos: int, tam_bloque: int,
                           backend: str = "numpy") -> float:
    """Crea los procesos, calcula y los destruye. Todo cuenta para el reloj."""
    indice = mp.Value("q", 0, lock=False)
    total = mp.Value("d", 0.0, lock=False)
    lock = mp.Lock()

    trabajadores = [
        mp.Process(
            target=_trabajador_efimero,
            args=(buffer, n, tam_bloque, backend, indice, total, lock),
            name=f"efimero-{i}",
        )
        for i in range(procesos)
    ]
    for p in trabajadores:
        p.start()
    for p in trabajadores:
        p.join()
    return float(total.value)


# Datos
def crear_buffer_compartido(n: int, semilla: int | None = None):
    """Reserva el vector en memoria compartida y lo llena.

    Se hace UNA vez, fuera de la región cronometrada.
    """
    buffer = RawArray("f", n)
    vista = np.frombuffer(buffer, dtype=np.float32, count=n)
    vista[:] = comun.crear_vector(n, semilla)
    return buffer, vista


def main() -> None:
    p = argparse.ArgumentParser(description="Suma paralela con procesos")
    p.add_argument("n", nargs="?", type=int, default=None)
    p.add_argument("procesos", nargs="?", type=int, default=None)
    p.add_argument("--backend", choices=list(comun.BACKENDS), default="numpy")
    p.add_argument("--tam-bloque", type=int, default=None)
    p.add_argument("--repeticiones", type=int, default=3)
    p.add_argument("--semilla", type=int, default=None)
    p.add_argument("--incluir-arranque", action="store_true",
                   help="crea y destruye los procesos dentro del cronómetro")
    args = p.parse_args()

    n = args.n or comun.n_por_defecto(args.backend)
    procesos = args.procesos or comun.hilos_disponibles()
    tam_bloque = args.tam_bloque or comun.tam_bloque_por_defecto(n, procesos)

    buffer, vista = crear_buffer_compartido(n, args.semilla)
    esperada = comun.suma_esperada(vista)

    print(f"n={n}  procesos={procesos}  backend={args.backend}  "
          f"tam_bloque={tam_bloque}  metodo_arranque={mp.get_start_method()}")

    if args.incluir_arranque:
        resultado, mediana, tiempos = comun.cronometrar(
            lambda: suma_paralela_procesos(buffer, n, procesos, tam_bloque, args.backend),
            args.repeticiones,
        )
        modo = "con arranque incluido"
    else:
        t_arranque = medir_arranque(buffer, n, procesos, args.backend)
        print(f"arranque de {procesos} procesos = {t_arranque:.4f} s "
              f"({t_arranque / procesos * 1000:.1f} ms por proceso) — NO se cuenta abajo")
        with PoolProcesos(buffer, n, procesos, args.backend) as pool:
            resultado, mediana, tiempos = comun.cronometrar(
                lambda: pool.sumar(tam_bloque), args.repeticiones
            )
        modo = "pool persistente"

    ok = comun.es_correcta(resultado, esperada)
    print(f"modo={modo}")
    print(f"suma={resultado:.6f}  esperada={esperada:.6f}  ok={ok}")
    print(f"t_mediana={mediana:.6f} s  (corridas={args.repeticiones}, "
          f"min={min(tiempos):.6f}, max={max(tiempos):.6f})")


if __name__ == "__main__":
    main()
