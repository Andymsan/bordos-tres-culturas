"""
Porcentaje de días de cada mes en que el nivel de la presa Endhó supera el bordo, por margen y por tramo.

Para cada margen se divide el perfil en tramos y se toma la cota mínima de cada uno:
es el punto por donde el agua entraría primero en ese tramo.

Uso:
  python temporada_por_margen.py niveles_endho.xlsx resultados [largo_tramo_m]
"""
import sys, glob, os
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

MESES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]


def main(niveles, carpeta, largo="100"):
    largo = float(largo)
    df = pd.read_excel(niveles, sheet_name="Gráfica Nivel Endhó", usecols=[1, 2])
    df.columns = ["fecha", "nivel"]
    df = df.dropna()
    df["fecha"] = pd.to_datetime(df["fecha"])
    df = df[(df.nivel > 1990) & (df.nivel < 2030)]
    niv_m = [np.sort(df[df.fecha.dt.month == m].nivel.values) for m in range(1, 13)]

    def pct_meses(z):
        return [100 * (len(s) - np.searchsorted(s, z, side="right")) / len(s) for s in niv_m]

    filas = []
    for ruta in sorted(glob.glob(f"{carpeta}/perfil_margen_*.csv")):
        lado = os.path.basename(ruta)[len("perfil_margen_"):-4]
        p = pd.read_csv(ruta).dropna(subset=["z_bordo"])
        i = p.z_bordo.idxmin()
        filas.append({"margen": lado, "tramo": "Margen completo", "dist_min_m": p.dist_m[i], "z_min": p.z_bordo[i],
                      **dict(zip(MESES, pct_meses(p.z_bordo[i])))})
        p["tramo"] = (p.dist_m // largo).astype(int)
        for t, g in p.groupby("tramo"):
            i = g.z_bordo.idxmin()
            filas.append({"margen": lado, "tramo": f"{t * largo:.0f}–{(t + 1) * largo:.0f}", "dist_min_m": g.dist_m[i],
                          "z_min": g.z_bordo[i], **dict(zip(MESES, pct_meses(g.z_bordo[i])))})
    tabla = pd.DataFrame(filas)
    tabla.round(2).to_csv(f"{carpeta}/temporada_por_margen.csv", index=False, encoding="utf-8-sig")

    lados = sorted(dict.fromkeys(tabla.margen), reverse=True)
    n = max((tabla.margen == l).sum() for l in lados)
    fig, axs = plt.subplots(1, len(lados), figsize=(7.5 * len(lados), 1.2 + 0.32 * n), squeeze=False, layout="constrained")
    for ax, lado in zip(axs[0], lados):
        t = tabla[tabla.margen == lado]
        M = t[MESES].values
        im = ax.imshow(M, cmap="YlGnBu", vmin=0, vmax=100, aspect="auto")
        for i in range(M.shape[0]):
            for j in range(M.shape[1]):
                v = M[i, j]
                ax.text(j, i, f"{v:.0f}" if v >= 1 else ("<1" if v > 0 else "·"), ha="center", va="center",
                        fontsize=8, color="white" if v > 60 else "#222")
        ax.axhline(0.5, color="k", lw=1.5)
        ax.set_xticks(range(12), MESES)
        ax.set_yticks(range(len(t)), [f"{a} · {z:.2f}" for a, z in zip(t.tramo, t.z_min)], fontsize=8)
        ax.set_title(f"Margen {lado.lower()}", fontsize=11)
    axs[0][0].set_ylabel("Tramo (m) · cota mínima (msnm)")
    fig.suptitle(f"Presa Endhó {df.fecha.dt.year.min()}–{df.fecha.dt.year.max()} · "
                 "% de días del mes con nivel por encima del punto más bajo de cada tramo", fontsize=11)
    fig.colorbar(im, ax=axs[0].tolist(), label="% de días", shrink=0.5)
    fig.savefig(f"{carpeta}/temporada_por_margen.png", dpi=150, bbox_inches="tight")


if __name__ == "__main__":
    main(*sys.argv[1:4])
