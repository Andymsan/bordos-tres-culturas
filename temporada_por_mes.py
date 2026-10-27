"""
Porcentaje de días de cada mes en que el nivel de la presa Endhó supera cada cota.

Uso:
  python temporada_por_mes.py niveles_endho.xlsx carpeta_salida
"""
import sys, os
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

COTAS = [2015, 2016, 2017, 2018, 2018.2, 2018.4, 2018.6, 2018.8, 2019, 2019.2]
MESES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]


def main(niveles, out):
    os.makedirs(out, exist_ok=True)
    df = pd.read_excel(niveles, sheet_name="Gráfica Nivel Endhó", usecols=[1, 2])
    df.columns = ["fecha", "nivel"]
    df = df.dropna()
    df["fecha"] = pd.to_datetime(df["fecha"])
    df = df[(df.nivel > 1990) & (df.nivel < 2030)]
    df["mes"] = df.fecha.dt.month
    tabla = pd.DataFrame({c: df.groupby("mes").nivel.apply(lambda s: (s > c).mean() * 100) for c in COTAS})
    tabla.index = MESES
    tabla.loc["Anual"] = [(df.nivel > c).mean() * 100 for c in COTAS]
    tabla.round(1).to_csv(f"{out}/temporada_por_mes.csv", encoding="utf-8-sig")

    M = tabla.loc[MESES, COTAS[::-1]].T.values
    fig, ax = plt.subplots(figsize=(11, 5.5))
    im = ax.imshow(M, cmap="YlGnBu", vmin=0, vmax=100, aspect="auto")
    for i in range(M.shape[0]):
        for j in range(M.shape[1]):
            v = M[i, j]
            ax.text(j, i, f"{v:.0f}" if v >= 1 else ("<1" if v > 0 else "·"), ha="center", va="center",
                    fontsize=9, color="white" if v > 60 else "#222")
    ax.set_xticks(range(12), MESES)
    ax.set_yticks(range(len(COTAS)), [f"{c:g}" for c in COTAS[::-1]])
    ax.set_ylabel("Cota (msnm)")
    ax.set_title(f"Presa Endhó {df.fecha.dt.year.min()}–{df.fecha.dt.year.max()} · "
                 "% de días del mes con nivel por encima de cada cota", fontsize=11)
    plt.colorbar(im, ax=ax, label="% de días")
    fig.tight_layout()
    fig.savefig(f"{out}/temporada_por_mes.png", dpi=150)


if __name__ == "__main__":
    main(*sys.argv[1:3])
