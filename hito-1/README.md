# Hito 1 — Concurrencia en CPU

**Materia:** Programación Concurrente 
**Institución:** Universidad Nacional de Guillermo Brown (UNaB), 2026  
**Integrantes:** Priscila Ohannecian · Agustín Barrientos · Marcelo Daniel Burgos  

**Objetivo:**
 demostrar dominio de hilos y sincronización.


---

## 1. Especificación del Problema 

**Suma de un vector grande.** Se mantiene el problema del esqueleto de la materia,
portado de C++ a Python. El vector es una lista de `1.0`, así que la suma esperada es
exactamente `N`.

---

## 2. Componentes del Entregable y Estructura

El módulo técnico del Hito 1 está compuesto por las siguientes unidades de código en **Python 3**:

| Archivo | Qué hace |
|---|---|
| `secuencial.py` | Referencia de un hilo: recorre el vector y acumula. |
| `paralelo-threading.py` | `GestorSumaParalela`: `threading` + cola dinámica de bloques protegida con `Lock`. |
| `benchmark.py` | Mide `T_seq` y `T(T)` para T = 1, 2, 4, 8, 16 e imprime `S(T) = T_seq / T(T)`. |
| `informe/informe.md` | Curva medida vs. Amdahl y análisis. |

### Sincronización

- Un índice compartido (`IndiceCompartido`) indica el próximo bloque libre.
- `SiguienteBloque()` lo lee y avanza dentro de `with self.Cerrojo:` (`threading.Lock`).
- La suma de cada bloque se hace **fuera** del lock, en una variable local del hilo.
- Cada hilo escribe su parcial en su propia posición de `ResultadoParcial`; al final
  `ejecutar()` hace `join()` de todos y suma los parciales.
---

## 3. Ejecución

Solo biblioteca estándar de Python 3, sin dependencias.

```bash
cd hito-1
python secuencial.py 16777216
python benchmark.py 16777216 3
```

`benchmark.py [N] [repeticiones]`. Por defecto N = 2²⁴ = 16 777 216 y 3 repeticiones,
y reporta la **mediana**. Salida:

```text
hardware_concurrency=8 N=16777216 repeticiones=5
hilos,ms,speedup,suma,correcto
seq,...
1,...
```

## 4. Criterio de "listo"

- [x] `secuencial` y `paralelo` dan la misma suma (`correcto=True`, total = N).
- [x] `paralelo` usa una primitiva de sincronización real (`threading.Lock`).
- [x] `benchmark` imprime T(T) y S(T) para varios T.
- [x] Informe con Amdahl y análisis: [`informe/informe.md`](informe/informe.md).
