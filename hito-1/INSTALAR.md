# Cómo dejar esto andando (Windows)

Guía paso a paso. **Después de cada paso hay un "tenés que ver"**: si eso no
aparece, no sigas — andá al final, a "Cuando algo falla".

Todo esto se hace **una sola vez** por computadora. Después, correr el proyecto
es sólo el paso 6.

---

## Paso 0 — ¿Qué es lo que vamos a hacer?

Tres cosas, en este orden:

1. Comprobar que la computadora tenga **Python** (el programa que ejecuta
   nuestro código).
2. Crear un **entorno virtual**: una carpeta donde se guardan las librerías que
   usa este proyecto, separadas del resto de la computadora. Así, si otra
   materia necesita otra versión de algo, no se pisan.
3. **Instalar las librerías** que el proyecto necesita (numpy y matplotlib).
   Están listadas en el archivo `requirements.txt`; no hay que nombrarlas una
   por una.

---

## Paso 1 — Abrir una terminal en la carpeta del proyecto

La "terminal" es la ventana negra (o azul) donde se escriben comandos. En
Windows se llama **PowerShell**.

1. Abrí el Explorador de archivos y entrá a la carpeta `hito-1`, la que tiene
   adentro los archivos `secuencial.py`, `paralelo.py`, etc.
2. Hacé clic en la **barra de direcciones** de arriba (donde dice la ruta),
   borrá lo que hay, escribí `powershell` y apretá Enter.

Se abre una ventana de texto ya parada en esa carpeta. Ese es el truco: si
abrís PowerShell desde el menú Inicio, arranca en otra carpeta y los comandos
no encuentran los archivos.

**Tenés que ver:** una ventana con una línea que termina en la ruta de tu
carpeta y un `>` al final. Algo así:

```
PS C:\Users\heenn\...\hito-1>
```

Todo lo que sigue se escribe ahí, y se aprieta Enter después de cada línea.

Para confirmar que estás parada en el lugar correcto, escribí:

```powershell
dir
```

**Tenés que ver:** una lista con `secuencial.py`, `paralelo.py`, `comun.py`,
`benchmark.py`, `requirements.txt`. Si no aparecen, estás en otra carpeta.

---

## Paso 2 — ¿Está Python instalado?

```powershell
py --version
```

**Tenés que ver:** algo como `Python 3.11.9` o un número mayor (3.12, 3.13…).

**Si dice que `py` no se reconoce como comando**, o si el número es menor a
3.11: hay que instalarlo.

1. Entrá a <https://www.python.org/downloads/> y bajá la versión para Windows.
2. Al abrir el instalador, **antes de tocar "Install"**, tildá abajo la casilla
   que dice **"Add python.exe to PATH"**. Es el paso que más se saltea y el que
   causa que después nada funcione.
3. Instalá, **cerrá la ventana de PowerShell y abrila de nuevo** (paso 1), y
   volvé a probar `py --version`.

> No uses la versión de Python de Microsoft Store: tiene problemas de permisos
> con las rutas y complica todo más adelante.

---

## Paso 3 — Crear el entorno virtual

```powershell
py -m venv .venv
```

Tarda unos segundos y **no imprime nada**. Eso está bien: en la terminal, "sin
noticias" es buena noticia.

**Tenés que ver:** que aparezca una carpeta nueva llamada `.venv` dentro de
`hito-1`. Comprobalo con:

```powershell
dir
```

(Si no la ves en el Explorador, es porque empieza con punto y Windows la
esconde. En la terminal sí aparece.)

---

## Paso 4 — Activar el entorno virtual

```powershell
.\.venv\Scripts\Activate.ps1
```

**Tenés que ver:** que el prompt ahora empiece con `(.venv)`:

```
(.venv) PS C:\Users\heenn\...\hito-1>
```

Ese `(.venv)` adelante es la señal de que está activado. **Si no está, los
comandos siguientes no van a funcionar como corresponde.**

**Si te tira un error largo en rojo** que menciona "no se puede cargar el
archivo" o "ExecutionPolicy": Windows bloquea scripts por seguridad. Pegá esto
y apretá Enter:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

No pide confirmación y no cambia nada permanente: vale sólo para esa ventana.
Después volvé a escribir la línea de `Activate.ps1`.

---

## Paso 5 — Instalar las librerías

Con el `(.venv)` visible adelante:

```powershell
pip install -r requirements.txt
```

Esto descarga numpy y matplotlib de internet. Tarda entre 30 segundos y 2
minutos, y escribe muchas líneas mientras trabaja.

**Tenés que ver** al final algo como:

```
Successfully installed matplotlib-3.x.x numpy-2.x.x ...
```

Si aparece un aviso amarillo sobre actualizar pip, ignoralo: es una sugerencia,
no un error.

---

## Paso 6 — Probar que funciona

```powershell
python secuencial.py 16777216
```

**Tenés que ver** tres líneas, y en la del medio, `ok=True`:

```
n=16777216  backend=numpy  tam_bloque=2097152
suma=16777216.000000  esperada=16777216.000000  ok=True
t_mediana=0.011296 s  (corridas=3, min=0.011152, max=0.011614)
```

Si ves `ok=True`, **terminaste**. Ya está todo instalado.

Ahora podés probar el resto:

```powershell
python paralelo.py 16777216 4
python paralelo_mp.py 16777216 4
python benchmark.py
python graficar.py
```

El `benchmark.py` es el que tarda (varios minutos) y deja `resultados.csv`.
`graficar.py` genera `speedup.png` a partir de ese CSV, así que va después.

---

## Cada vez que vuelvas a trabajar

Los pasos 2 a 5 son de una sola vez. Cuando abras la computadora otro día:

1. Abrí PowerShell en la carpeta `hito-1` (paso 1).
2. Activá el entorno (paso 4): `.\.venv\Scripts\Activate.ps1`
3. Corré lo que necesites.

**El error más común de todos** es olvidarse el paso 2 y que Python diga
`ModuleNotFoundError: No module named 'numpy'`. No es que numpy se haya
desinstalado: es que el entorno no está activado. Fijate si tenés el `(.venv)`
adelante.

---

## Cuando algo falla

| Lo que dice la pantalla | Qué pasa | Cómo se arregla |
|---|---|---|
| `py no se reconoce como un comando` | Python no está instalado, o se instaló sin tildar "Add to PATH" | Reinstalar desde python.org tildando esa casilla, y **abrir una terminal nueva** |
| `no se puede cargar el archivo ... Activate.ps1` | Windows bloquea scripts | `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` y reintentar |
| `ModuleNotFoundError: No module named 'numpy'` | El entorno no está activado | Paso 4. Mirá que aparezca `(.venv)` |
| `No such file or directory: 'secuencial.py'` | La terminal está parada en otra carpeta | Paso 1. Verificá con `dir` |
| `pip no se reconoce como un comando` | El entorno no está activado | Paso 4 |
| El `pip install` se cuelga o falla a la mitad | Conexión, o OneDrive sincronizando | Reintentar; ver la nota de OneDrive abajo |
| `MemoryError` al correr con N grande | El vector no entra en RAM | Usar un N más chico: `python secuencial.py 4000000` |

Si el error no está en esta tabla, **copiá el texto completo del error** y
pedí ayuda con eso pegado. El mensaje de error dice qué pasó; adivinar sin
leerlo es el camino largo.

---

## Nota sobre OneDrive

Si la carpeta del proyecto está dentro de OneDrive, tené en cuenta que el
`.venv` son miles de archivos chicos que OneDrive va a intentar sincronizar a
la nube. Eso lo hace lento y a veces hace fallar el `pip install` con errores
de "archivo en uso".

Lo más simple es mover el proyecto fuera de OneDrive, por ejemplo a
`C:\Users\<tu usuario>\proyecto-concu`. Sobre todo cuando clonen el repositorio
del grupo: un repo de git dentro de OneDrive da problemas.

Si preferís no mover nada: clic derecho sobre la carpeta `.venv` → "Liberar
espacio", para que OneDrive no la mantenga sincronizada.

---

## Para macOS o Linux

Los mismos pasos, con estos comandos:

```bash
python3 --version
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python secuencial.py 16777216
```

No hace falta tocar ninguna política de ejecución.
