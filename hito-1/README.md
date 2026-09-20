# Hito 1 — Concurrencia en CPU

**Materia:** Programación Concurrente 
**Institución:** Universidad Nacional de Guillermo Brown (UNaB), 2026  
**Integrantes:** Priscila Ohannecian · Agustín Barrientos · Marcelo Daniel Burgos  

**Objetivo:**
 demostrar dominio de hilos y sincronización.


---

## 1. Especificación del Problema (Paralelismo de Datos)

El desarrollo aborda el problema de la **reducción por suma de un vector unidimensional grande de tipo `float32`**. El diseño de la arquitectura del software de medición se estructuró bajo las siguientes especificaciones técnicas para garantizar condiciones científicas y estricta correctitud:

*   **Evitación de Estancamiento en Punto Flotante:** Para el cálculo de acumulaciones sobre volúmenes masivos de datos ($N = 67.108.864$), la reducción se ejecuta utilizando acumuladores locales y globales en **`float64`**. Trabajar exclusivamente en precisión simple (`float32`) provocaría la pérdida de significancia numérica y el estancamiento de la suma al aproximarse al límite de redondeo estructural de la mantisa a partir de $2^{24}$ ($16.777.216$) elementos.
*   **Balanceo Dinámico de Carga:** En lugar de implementar un particionamiento estático y rígido del vector, los trabajadores consumen rangos de datos `[ini, fin)` bajo demanda mediante una estructura de **cola dinámica** compartida. Esto asegura una distribución óptima frente a imprevistos de planificación del sistema operativo (*desalojos de hilos*) o asimetrías de hardware, optimizando la eficiencia en escenarios de sobre-suscripción.
*   **Secciones Críticas Mínimas:** El algoritmo restringe el uso de primitivas de exclusión mutua (`Lock`) al mínimo indispensable. Los trabajadores realizan las sumas masivas sobre registros y variables locales **fuera del lock**, accediendo de manera segura a las variables globales únicamente en dos puntos críticos:
    1.  Para adquirir el próximo bloque de trabajo de la cola dinámica compartida.
    2.  Para consolidar el acumulado parcial local en el acumulador global una sola vez al finalizar su ciclo (*reducción privada*).

---

## 2. Componentes del Entregable y Estructura

El módulo técnico del Hito 1 está compuesto por las siguientes unidades de código en **Python 3**:

*   `comun.py`: Núcleo matemático y utilitario compartido. Define las funciones de generación de vectores, los backends de cálculo, y las ecuaciones experimentales para el ajuste de mínimos cuadrados de Amdahl y la métrica de Karp-Flatt.
*   `secuencial.py`: Establece el tiempo base de referencia uniproceso ($T_{\mathrm{seq}}$). Utiliza la misma estrategia de segmentación por bloques fijos que los algoritmos concurrentes para asegurar una comparación de rendimiento computacional directo y transparente.
*   `paralelo.py`: Implementación multi-hilo nativa utilizando la biblioteca `threading`. Integra control de exclusión mutua por lock para evaluar la contención y la liberación del GIL.
*   `paralelo_mp.py`: Implementación multi-proceso nativa utilizando `multiprocessing`. Evita la serialización del intérprete mapeando el vector directamente en un segmento de memoria física compartida sin copia (`RawArray`).
*   `benchmark.py`: Arnés de automatización encargado de realizar los barridos empíricos variando el nivel de paralelismo de trabajadores ($T \in [1, 2, 4, 8, 16]$) bajo configuraciones repetibles. Genera los archivos de auditoría `resultados.csv` y `entorno.txt`.
*   `graficar.py`: Script de visualización que procesa los datos tabulados y genera el panel de curvas de aceleración experimental contra los techos analíticos de Amdahl (`speedup.png`).

---

## 3. Criterio de "Listo" y Verificación de Correctitud

Para cumplir con las directrices académicas de validación, el entorno implementa mecanismos estrictos de control:

*   **Validación de Resultados:** Cada una de las 24 variantes y ejecuciones del benchmark verifica de forma automatizada que la suma total obtenida coincida exactamente con la referencia secuencial pura, aplicando una función de tolerancia relativa estricta a nivel binario de $10^{-9}$ (`comun.es_correcta`). Todos los puntos registrados arrojaron estado de validación verificado (`ok=True`).
*   **Sincronización Real de Datos:** Se han eliminado por completo las esperas pasivas y los marcadores de posición temporales (*placeholders*). Las secciones críticas están estrictamente protegidas contra condiciones de carrera, garantizando consistencia determinista en la memoria concurrente.

---

## 4. Datos del Entorno de Ejecución (Hardware de Prueba)

Todas las mediciones que sustentan el análisis teórico fueron capturadas de manera local y determinista bajo la siguiente arquitectura de hardware y sistema operativo:

*   **Procesador:** Intel Core i7-6700 (Skylake) @ 3.40 GHz.
*   **Configuración de Núcleos:** 4 núcleos físicos / 8 núcleos lógicos (Tecnología Hyper-Threading).
*   **Memoria RAM:** 16 GB (2 × 8 GB DDR4-2133 MHz) operando en configuración de Doble Canal.
*   **Ancho de Banda Teórico Máximo del Bus:** 34.1 GB/s.
*   **Sistema Operativo:** Windows 10 Pro (Versión 10.0.19045).
*   **Intérprete y Librerías:** CPython 3.14.6 con NumPy 2.5.3 (Método de arranque de subprocesos: `spawn`).

---

## 5. Instrucciones de Despliegue y Ejecución

No se requiere una fase previa de compilación de binarios al tratarse de un entorno interpretado en Python 3. Ejecute los siguientes comandos en su terminal de comandos para inicializar el entorno aislado, instalar las dependencias de análisis matemático y reproducir los barridos empíricos:

```bash
# 1. Navegar al directorio del hito y crear el entorno virtual aislado
cd hito-1
python -m venv .venv

# 2. Activar el entorno virtual (Elegir según su consola y Sistema Operativo)
# Windows (PowerShell):
.\.venv\Scripts\Activate.ps1
# Windows (Git Bash / Linux / macOS):
source .venv/bin/activate

# 3. Instalar dependencias requeridas (NumPy y Matplotlib)
pip install -r requirements.txt

# 4. Ejecutar el arnés de benchmark automatizado (7 repeticiones por punto)
python benchmark.py --n 67108864 --n-puro 4000000 --repeticiones 7

# 5. Generar los paneles gráficos de aceleración analítica
python graficar.py
```
## 6. Documentación Adicional

**Análisis Teórico Completo:** Para examinar el estudio pormenorizado sobre la saturación de los núcleos físicos versus lógicos, la métrica de Karp-Flatt, el impacto de la serialización del GIL en CPython y la amortización del costo de arranque (spawn) de procesos, consultar el entregable principal: informe/informe.md.
