# Hito 1 — Concurrencia en CPU

**Materia:** Programación Concurrente — UNaB, 2026
**Integrantes:** Priscila Ohannecian · Agustín Barrientos · Marcelo Daniel Burgos
**Fecha:** _(entrega, Clase 4)_

---

## 1. Problema y diseño

Suma de un vector de `1.0` de tamaño N (resultado esperado: N), en Python.

- `secuencial.py`: bucle `for` que acumula.
- `paralelo-threading.py`: T hilos toman bloques de 2¹⁶ elementos de una cola dinámica.
  El índice de la cola se protege con `threading.Lock`. Cada hilo suma fuera del lock y
  guarda su parcial en una posición propia. Al final, `join()` y suma de parciales.


## 2. Metodología

i7-6700 (4 físicos / 8 lógicos), Windows 10, CPython 3.14.
`python benchmark.py 16777216` → N = 2²⁴, mediana de 3 corridas. La creación y el `join()`
de los hilos entran en la medición. Todas las corridas dan `suma = N`.

## 3. Resultados

`hardware_concurrency = 8` · `T_seq = 1050,7 ms`

| T | T(T) (ms) | S(T) medido | Amdahl s=0,05 | s=0,5 | s=0,95 |
|---|---|---|---|---|---|
| 1 | 1417,1 | 0,74 | 1,00 | 1,00 | 1,00 |
| 2 | 1402,5 | 0,75 | 1,90 | 1,33 | 1,03 |
| 4 | 1407,7 | 0,75 | 3,48 | 1,60 | 1,04 |
| 8 | 1375,6 | 0,76 | 5,93 | 1,78 | 1,05 |
| 16 | 1377,4 | 0,76 | 9,14 | 1,88 | 1,05 |

Amdahl: `S(T) = 1 / (s + (1 − s) / T)`, con `s` barrido.

## 4. Análisis

- **GIL:** en CPython un solo hilo ejecuta bytecode a la vez. Los hilos se turnan y no
  suman en paralelo: T(T) queda en ~1,4 s para cualquier T y S(T) es plano (0,74–0,76).
- **Debajo de Amdahl:** Amdahl nunca da menos de 1, ni con `s = 1`. La curva medida
  queda por debajo porque la versión paralela tiene costo extra que Amdahl no modela.
- **S(1) = 0,74:** con un solo hilo ya es ~35 % más lenta. Accede por índice (más caro
  que iterar la lista), toma el `Lock` por bloque y paga la creación y el `join()` del hilo.
- **Más hilos:** de T = 1 a T = 16 el tiempo apenas baja (1417 → 1377 ms, ~3 %), dentro
  del ruido. No hay cálculo simultáneo que aprovechar los 8 núcleos lógicos.
- **BLOQUE = 2¹⁶:** 256 accesos al `Lock` contra 16 M de sumas; la sincronización
  pesa poco y la carga queda balanceada.

## 5. Aprendizajes

La sincronización es correcta: siempre da N. No hay aceleración porque el GIL impide
ejecutar bytecode en paralelo, y la versión paralela queda entre 31 % y 35 % más lenta
que la secuencial por el costo de indexar, sincronizar y crear hilos. `threading` en
CPython no acelera cálculo puro.
