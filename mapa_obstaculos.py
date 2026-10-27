import sys, glob, os
import numpy as np, pandas as pd, geopandas as gpd, rasterio
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LightSource
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
from rasterio.windows import from_bounds
from bordo_analisis import SEMIANCHO, PASO

COLOR = {"árbol": "#2e9e44", "edificio": "#e0590c"}


def main(mdt, carpeta, png):
    g = f"{carpeta}/bordo_analisis.gpkg"
    ob = gpd.read_file(g, layer="obstaculos")
    bordo = gpd.read_file(g, layer="bordo")
    b = bordo.total_bounds
    bx = (b[0] - 60, b[1] - 60, b[2] + 60, b[3] + 60)
    with rasterio.open(mdt) as r:
        w = from_bounds(*bx, r.transform)
        f = max(1, int(w.width / 1400))
        z = r.read(1, window=w, out_shape=(int(w.height / f), int(w.width / f))).astype(float)
        res = r.res[0] * f
    z[z < 1900] = np.nan
    hs = LightSource(315, 45).hillshade(np.nan_to_num(z, nan=2015), vert_exag=3, dx=res, dy=res)

    perfiles = {}
    for ruta in sorted(glob.glob(f"{carpeta}/perfil_margen_*.csv"), reverse=True):
        p = pd.read_csv(ruta)
        pts = gpd.GeoDataFrame(p, geometry=gpd.points_from_xy(p.x, p.y), crs=ob.crs)
        sobre = ob[ob.sobre_bordo == "sí"]
        p["tipo"] = "no"
        for tipo in ("árbol", "edificio"):
            t = sobre[sobre.tipo == tipo]
            if len(t):
                p.loc[pts.buffer(SEMIANCHO).intersects(t.union_all()).values, "tipo"] = tipo
        perfiles[os.path.basename(ruta)[len("perfil_margen_"):-4]] = p

    fig = plt.figure(figsize=(16, 13))
    gs = fig.add_gridspec(len(perfiles) + 1, 2, width_ratios=[1.1, 1], height_ratios=[1] * len(perfiles) + [1.4])
    ax = fig.add_subplot(gs[:, 0])
    ax.imshow(hs, cmap="gray", extent=[bx[0], bx[2], bx[1], bx[3]])
    for tipo, c in COLOR.items():
        t = ob[ob.tipo == tipo]
        t[t.sobre_bordo == "no"].plot(ax=ax, color=c, alpha=0.35, lw=0)
        t[t.sobre_bordo == "sí"].plot(ax=ax, color=c, edgecolor="k", lw=0.4)
    bordo.plot(ax=ax, color="#1d74c9", lw=1.6)
    for lado, p in perfiles.items():
        for d in range(0, int(p.dist_m.max()), 500):
            q = p.iloc[(p.dist_m - d).abs().argmin()]
            ax.annotate(f"{d}", (q.x, q.y), fontsize=7, color="#1d74c9", weight="bold",
                        xytext=(-14 if lado == "Izquierda" else 4, 0), textcoords="offset points")
    ax.legend(handles=[Line2D([0], [0], color="#1d74c9", lw=2, label="Bordo (m desde aguas arriba)"),
                       Patch(color=COLOR["árbol"], label="Árbol sobre el bordo"),
                       Patch(color=COLOR["árbol"], alpha=0.35, label="Árbol cerca (≤ 40 m)"),
                       Patch(color=COLOR["edificio"], label="Edificio sobre el bordo"),
                       Patch(color=COLOR["edificio"], alpha=0.35, label="Edificio cerca (≤ 40 m)")],
              loc="lower left", fontsize=9)
    ax.set_xlim(bx[0], bx[2]); ax.set_ylim(bx[1], bx[3])
    ax.ticklabel_format(useOffset=False, style="plain")
    ax.tick_params(labelsize=7)
    ax.set_title("Árboles y edificios detectados (MDT + Sentinel-2 + Open Buildings)", fontsize=11)

    filas = []
    for k, (lado, p) in enumerate(perfiles.items()):
        a = fig.add_subplot(gs[k, 1])
        a.plot(p.dist_m, p.z_bordo, color="#1d74c9", lw=1.5)
        for tipo, c in COLOR.items():
            m = (p.tipo == tipo).values
            a.fill_between(p.dist_m, 2015.5, 2021, where=m, color=c, alpha=0.35, lw=0, step="mid")
            filas.append((lado, tipo, m.sum() * PASO))
        a.set_xlim(0, p.dist_m.max()); a.set_ylim(2016.5, 2021)
        a.set_ylabel("msnm"); a.grid(alpha=0.3)
        a.set_title(f"Margen {lado.lower()} · franjas = tramos tapados", fontsize=10)
    a.set_xlabel("Distancia a lo largo del bordo (m)")

    a = fig.add_subplot(gs[-1, 1])
    t = pd.DataFrame(filas, columns=["margen", "tipo", "m"]).pivot(index="margen", columns="tipo", values="m")
    t = t.reindex(columns=list(COLOR)).fillna(0)
    t.plot.barh(ax=a, color=[COLOR[c] for c in t.columns], width=0.6)
    for cont in a.containers:
        a.bar_label(cont, fmt="%.0f m", fontsize=9, padding=3)
    a.set_xlabel("Metros de bordo tapados"); a.set_ylabel(""); a.legend(title="")
    a.set_xlim(0, max(1, t.values.max()) * 1.25)
    a.set_title("Total por margen", fontsize=10)

    fig.tight_layout()
    fig.savefig(png, dpi=120)


if __name__ == "__main__":
    main(*sys.argv[1:4])
