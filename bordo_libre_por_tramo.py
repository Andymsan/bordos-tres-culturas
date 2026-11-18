import sys, glob, os
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from bordo_analisis import NAME, CLASES, COLORES, BORDO_LIBRE_MIN, IMTA_A_ENDHO, clase_de


def main(niveles, carpeta, largo="100"):
    largo = float(largo)
    df = pd.read_excel(niveles, sheet_name="Gráfica Nivel Endhó", usecols=[1, 2])
    df.columns = ["fecha", "nivel"]
    df = df.dropna()
    df["fecha"] = pd.to_datetime(df["fecha"])
    df = df[(df.nivel > 1990) & (df.nivel < 2030)]
    i = df.nivel.idxmax()
    max_hist, f_max = df.nivel[i], df.fecha[i]

    filas = []
    for ruta in sorted(glob.glob(f"{carpeta}/perfil_margen_*.csv")):
        lado = os.path.basename(ruta)[len("perfil_margen_"):-4]
        p = pd.read_csv(ruta).dropna(subset=["z_bordo"])
        p["tramo"] = (p.dist_m // largo).astype(int)
        for t, g in p.groupby("tramo"):
            j = g.z_bordo.idxmin()
            z = g.z_bordo[j]
            filas.append({"margen": lado, "tramo": f"{t * largo:.0f}–{(t + 1) * largo:.0f}", "desde_m": t * largo,
                          "dist_min_m": g.dist_m[j], "z_min": z, "z_min_mde": z - IMTA_A_ENDHO,
                          "bordo_libre_m": z - NAME, "sobre_max_hist_m": z - max_hist, "clase": clase_de(z)})
    tabla = pd.DataFrame(filas)
    tabla.drop(columns="desde_m").round(2).to_csv(f"{carpeta}/bordo_libre_por_tramo.csv", index=False, encoding="utf-8-sig")

    lados = sorted(dict.fromkeys(tabla.margen), reverse=True)
    fig, axs = plt.subplots(len(lados), 1, figsize=(16, 3.6 * len(lados)), squeeze=False, sharey=True, layout="constrained")
    limites = [c[0] for c in CLASES] + [CLASES[-1][1]]
    for ax, lado in zip(axs[:, 0], lados):
        t = tabla[tabla.margen == lado]
        col = [COLORES[min(np.searchsorted(limites, z, side="right") - 1, len(CLASES) - 1)] for z in t.z_min]
        ax.bar(t.desde_m + largo / 2, t.bordo_libre_m, width=largo * 0.85, color=col, edgecolor="#333", lw=0.4)
        for x, v in zip(t.desde_m + largo / 2, t.bordo_libre_m):
            ax.text(x, v + 0.05, f"{v:.2f}", ha="center", va="bottom", fontsize=7)
        ax.axhline(BORDO_LIBRE_MIN, ls="--", lw=1, color="darkred")
        ax.text(10, BORDO_LIBRE_MIN + 0.06, f"bordo libre mínimo {BORDO_LIBRE_MIN:g} m",
                ha="left", va="bottom", fontsize=9, color="darkred", bbox=dict(fc="white", ec="none", pad=1, alpha=0.85))
        ax.axhline(max_hist - NAME, ls=":", lw=1, color="#1d74c9")
        ax.text(t.desde_m.max() + largo, max_hist - NAME + 0.04,
                f"nivel máximo registrado {max_hist:.2f} ({f_max:%d/%m/%Y})", ha="right", va="bottom", fontsize=9, color="#1d74c9")
        ax.axhline(0, color="k", lw=1)
        ax.set_xlim(0, t.desde_m.max() + largo)
        ax.set_ylim(min(-1.0, max_hist - NAME - 0.3), tabla.bordo_libre_m.max() + 0.5)
        ax.set_ylabel("Bordo libre sobre\nel NAME (m)")
        ax.set_title(f"Margen {lado.lower()} · punto más bajo de cada tramo de {largo:g} m", fontsize=11)
        ax.grid(axis="y", alpha=0.3)
    axs[-1, 0].set_xlabel("Distancia a lo largo del bordo (m, desde aguas arriba)")
    fig.suptitle(f"Bordo libre: cota mínima del bordo − NAME {NAME:g} msnm datum Endhó ({NAME - IMTA_A_ENDHO:.2f} en el MDE) · "
                 f"niveles {df.fecha.dt.year.min()}–{df.fecha.dt.year.max()}", fontsize=11)
    fig.savefig(f"{carpeta}/bordo_libre_por_tramo.png", dpi=150)


if __name__ == "__main__":
    main(*sys.argv[1:4])
