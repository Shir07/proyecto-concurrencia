"""
GRÁFICO — curva de aceleración medida vs. Ley de Amdahl.

Lee `resultados.csv` y genera un panel por combinación (backend x ejecución).
En cada panel:

  - aceleración MEDIDA (línea sólida con marcadores)
  - curva de AMDAHL con el `s` ajustado a esas mediciones (línea punteada)
  - aceleración IDEAL S(T) = T (línea gris fina, referencia)
  - una banda vertical donde empieza la sobre-suscripción (T > núcleos)

Cuatro paneles chicos en vez de doce series en un solo eje: cada combinación
tiene su propia escala y su propio `s`, mezclarlas haría el gráfico ilegible.

Uso:
    python graficar.py
    python graficar.py --csv resultados.csv --salida speedup.png
"""

from __future__ import annotations

import argparse
import csv
import math

import matplotlib

matplotlib.use("Agg")           # sin ventana: sólo escribe el archivo
import matplotlib.pyplot as plt

import comun

# Paleta validada para daltonismo y para impresión en escala de grises
# (el azul y el naranja también se distinguen por estilo de línea y marcador).
COLOR_MEDIDO = "#1B6FB5"
COLOR_AMDAHL = "#C8641A"
COLOR_IDEAL = "#9AA0A6"
COLOR_TEXTO = "#202124"
COLOR_TENUE = "#5F6368"

TITULOS = {
    "numpy-hilos": "NumPy + hilos",
    "numpy-procesos": "NumPy + procesos",
    "puro-hilos": "Python puro + hilos",
    "puro-procesos": "Python puro + procesos",
}


def leer(csv_path: str) -> dict[str, list[dict]]:
    grupos: dict[str, list[dict]] = {}
    with open(csv_path, newline="", encoding="utf-8") as fh:
        for fila in csv.DictReader(fh):
            if int(fila["hilos"]) == 0:      # la fila secuencial de referencia
                continue
            grupos.setdefault(fila["combinacion"], []).append(fila)
    for filas in grupos.values():
        filas.sort(key=lambda f: int(f["hilos"]))
    return grupos


def ajustar_s(puntos: list[tuple[int, float]]) -> float:
    mejor_s, mejor_err = 1.0, float("inf")
    for i in range(1, 10_001):
        s = i / 10_000
        err = sum((comun.amdahl(s, t) - medido) ** 2 for t, medido in puntos)
        if err < mejor_err:
            mejor_s, mejor_err = s, err
    return mejor_s


def dibujar_panel(ax, combinacion: str, filas: list[dict], nucleos: int) -> float:
    hilos = [int(f["hilos"]) for f in filas]
    medidos = [float(f["speedup"]) for f in filas]
    s = ajustar_s(list(zip(hilos, medidos)))

    if max(hilos) > nucleos:
        ax.axvspan(nucleos, max(hilos), color="#000000", alpha=0.04, lw=0)
        ax.text(nucleos * 1.05, 0.02, "sobre-suscripción", fontsize=7,
                color=COLOR_TENUE, va="bottom", transform=ax.get_xaxis_transform())

    ax.plot(hilos, hilos, color=COLOR_IDEAL, lw=1, ls=(0, (1, 2)),
            label="ideal  S(T) = T", zorder=1)

    finos = [1 + i * (max(hilos) - 1) / 200 for i in range(201)]
    ax.plot(finos, [comun.amdahl(s, t) for t in finos], color=COLOR_AMDAHL,
            lw=2, ls="--", label=f"Amdahl  s = {s:.3f}", zorder=2)

    ax.plot(hilos, medidos, color=COLOR_MEDIDO, lw=2, marker="o", ms=5,
            mec="white", mew=1.2, label="medido", zorder=3)

    # Etiqueta directa sólo en el último punto: nunca un número en cada punto.
    ax.annotate(f"{medidos[-1]:.2f}x", (hilos[-1], medidos[-1]),
                textcoords="offset points", xytext=(6, -2), fontsize=8,
                color=COLOR_TEXTO, ha="left", va="center")

    n = int(filas[0]["n"])
    ax.set_title(f"{TITULOS.get(combinacion, combinacion)}   (N = {n:,})".replace(",", " "),
                 fontsize=10, color=COLOR_TEXTO, pad=8, loc="left")
    ax.set_xscale("log", base=2)
    ax.set_xticks(hilos)
    ax.set_xticklabels([str(h) for h in hilos])
    ax.set_xlabel("hilos / procesos (T)", fontsize=9, color=COLOR_TENUE)
    ax.set_ylabel("aceleración S(T)", fontsize=9, color=COLOR_TENUE)
    ax.set_ylim(0, max(max(medidos), comun.amdahl(s, max(hilos))) * 1.25 + 0.2)
    ax.grid(True, color="#E3E3E0", lw=0.6)
    ax.set_axisbelow(True)
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)
    for lado in ("left", "bottom"):
        ax.spines[lado].set_color("#C9C9C4")
    ax.tick_params(colors=COLOR_TENUE, labelsize=8)
    ax.legend(fontsize=8, frameon=False, loc="upper left", labelcolor=COLOR_TEXTO)
    return s


def main() -> None:
    p = argparse.ArgumentParser(description="Gráfico medido vs. Amdahl")
    p.add_argument("--csv", default="resultados.csv")
    p.add_argument("--salida", default="speedup.png")
    args = p.parse_args()

    grupos = leer(args.csv)
    if not grupos:
        raise SystemExit(f"{args.csv} no tiene filas paralelas. Corré benchmark.py primero.")

    nucleos = comun.hilos_disponibles()
    orden = [c for c in ["numpy-hilos", "numpy-procesos", "puro-hilos", "puro-procesos"]
             if c in grupos]
    filas_grilla = math.ceil(len(orden) / 2)
    cols = 2 if len(orden) > 1 else 1

    fig, axes = plt.subplots(filas_grilla, cols,
                             figsize=(5.2 * cols, 3.9 * filas_grilla))
    fig.patch.set_facecolor("#FCFCFB")
    ejes = list(axes.flat) if hasattr(axes, "flat") else [axes]

    estimados = {}
    for ax, combinacion in zip(ejes, orden):
        ax.set_facecolor("#FCFCFB")
        estimados[combinacion] = dibujar_panel(ax, combinacion, grupos[combinacion], nucleos)
    for ax in ejes[len(orden):]:
        ax.set_visible(False)

    fig.suptitle(f"Hito 1 — aceleración medida vs. Ley de Amdahl  "
                 f"({nucleos} núcleos lógicos)",
                 fontsize=12, color=COLOR_TEXTO, x=0.01, ha="left", y=0.995)
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    fig.savefig(args.salida, dpi=200, facecolor=fig.get_facecolor())
    print(f"Gráfico escrito en {args.salida}")
    print("\nFracción secuencial ajustada por combinación (para el informe):")
    for combinacion, s in estimados.items():
        print(f"  {combinacion:16s} s = {s:.4f}   techo de Amdahl = {1 / s:6.2f}x")


if __name__ == "__main__":
    main()
