# Hito 1 — Concurrencia en CPU 

Repositorio correspondiente al proyecto práctico de la materia *Programación Concurrente*.

---

## 🏛️ Institución
- *Universidad:* Universidad Nacional de Guillermo Brown (UNaB)
- *Materia:* Programación Concurrente 
- *Año:* 2026

---

## 📌 Descripción General
Este repositorio contendrá el desarrollo del proyecto grupal enfocado en la resolución de problemas mediante concurrencia, sincronización de procesos/hilos y gestión de recursos compartidos.


---

## 👥 Integrantes
| Nombre y Apellido | GitHub |
| :--- | :--- |
| *Priscila Ohannecian* | [@Shir07](https://github.com/Shir07) |
| *Agustín Barrientos* | [@dante-ww](https://github.com/dante-ww) |
| *Marcelo Daniel Burgos* | [@Marcelo2120](https://github.com/Marcelo2120) |


---

## 🛠️ Estado del Proyecto
- [x] Creación del repositorio y organización inicial
- [x] Desarrollo del Hito 1

## Hitos

| Hito | Contenido | Entrega | Peso | Estado |
|---|---|---|---|---|
| [1 — Concurrencia CPU](hito-1/) | Secuencial, paralelo, benchmark, informe | Clase 4 | 12 % | ✅ completo |
| [2 — Kernels CUDA](hito-2/) | Kernels con Numba, datos de perfilado | Clase 7 | 15 % | ⬜ pendiente |
| [3 — LLM local + métricas](hito-3/) | Instalación, CSV de mediciones, informe | Clase 9 | 15 % | ⬜ pendiente |
| [4 — Integración y defensa](hito-4/) | Bitácora de perfilado, informe global | Clase 12 | 18 % | ⬜ pendiente |

## Hardware

| | |
|---|---|
| CPU | Intel Core i7-6700 @ 3,40 GHz (Skylake) |
| Núcleos | **4 físicos / 8 lógicos** (hyper-threading) |
| RAM | 16 GB — 2 × 8 GB DDR4-2133, doble canal |
| Ancho de banda teórico de memoria | 34,1 GB/s |
| GPU | NVIDIA GeForce GTX 1660 SUPER — 6 GB GDDR6 |
| Compute capability | **7.5** (arquitectura Turing) |
| Relación FP32/FP64 | 32:1 — la doble precisión corre a 1/32 de la simple |
| SO | Windows 10 Pro 10.0.19045 |

Salida completa de `nvidia-smi`: [`hito-2/nvidia-smi.txt`](hito-2/nvidia-smi.txt).

> La distinción entre núcleos **físicos** y **lógicos** resultó central en el
> Hito 1: `os.cpu_count()` devuelve 8, pero el paralelismo de cálculo real tope
> es 4. Ver el análisis en [`hito-1/informe/informe.md`](hito-1/informe/informe.md).

## Software

| | |
|---|---|
| Python | 3.14 |
| NumPy | 2.5.3 |

## Cómo correr

No hay compilación: el proyecto es Python. Cada hito trae su propio
`requirements.txt`.

```bash
cd hito-1
python -m venv .venv
```

Activar el entorno — Windows (PowerShell):

```powershell
.\.venv\Scripts\Activate.ps1
```

macOS / Linux:

```bash
source .venv/bin/activate
```

Instalar y correr:

```bash
pip install -r requirements.txt
python benchmark.py --n 67108864 --n-puro 4000000 --repeticiones 7
python graficar.py
```

---

## Estructura del repositorio

```text
README.md                 ← este archivo
hito-1/                   ← secuencial, paralelo, benchmark, informe
  comun.py                ← núcleo compartido: vector, backends, Amdahl, Karp-Flatt
  secuencial.py           ← referencia de un hilo (T_seq)
  paralelo.py             ← hilos + cola dinámica con Lock
  paralelo_mp.py          ← procesos + memoria compartida
  benchmark.py            ← barrido completo → resultados.csv, entorno.txt
  graficar.py             ← resultados.csv → speedup.png
  informe/informe.md      ← entregable del hito
hito-2/                   ← (próximo)kernels con Numba, datos de perfilado
hito-3/                   ← (próximo)instalar.md, CSV de mediciones, informe
hito-4/                   ← (próximo)integración, bitácora de perfilado, informe global
informes/                 ← informe en pdf
```

Los resultados (`resultados.csv`, `speedup.png`, `entorno.txt`) **se versionan**:
son la evidencia de los informes, no archivos descartables.

