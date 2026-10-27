import sys
import numpy as np, geopandas as gpd, rasterio
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LightSource
from matplotlib.lines import Line2D
from rasterio.windows import from_bounds
from bordo_analisis import CLASES


def main(mdt, gpkg, png):
    seg = gpd.read_file(gpkg, layer="bordo_por_cota")
    bajos = gpd.read_file(gpkg, layer="puntos_bajos")
    b = seg.total_bounds
    bx = (b[0] - 60, b[1] - 60, b[2] + 60, b[3] + 60)
    with rasterio.open(mdt) as r:
        w = from_bounds(*bx, r.transform)
        f = max(1, int(w.width / 1400))
        z = r.read(1, window=w, out_shape=(int(w.height / f), int(w.width / f))).astype(float)
        res = r.res[0] * f
    z[z < 1900] = np.nan
    ext = [bx[0], bx[2], bx[1], bx[3]]
    hs = LightSource(315, 45).hillshade(np.nan_to_num(z, nan=2015), vert_exag=3, dx=res, dy=res)

    alto = 13 * (bx[3] - bx[1]) / (bx[2] - bx[0])
    fig, ax = plt.subplots(figsize=(13, max(6, min(20, alto))))
    ax.imshow(hs, cmap="gray", extent=ext)
    ax.imshow(np.ma.masked_invalid(z), cmap="Greys_r", vmin=2010, vmax=2024, alpha=0.35, extent=ext)
    colores = {c[2]: c[3] for c in CLASES}
    seg.plot(ax=ax, color=[colores[c] for c in seg.clase], linewidth=3)
    criticos = bajos[bajos.z_min < 2018.0]
    ax.scatter(criticos.geometry.x, criticos.geometry.y, marker="^", s=90, c="red", edgecolors="k", zorder=5)
    for _, r in criticos.iterrows():
        ax.annotate(f"{r.id}: {r.z_min:.2f}", (r.geometry.x, r.geometry.y), xytext=(5, -9),
                    textcoords="offset points", fontsize=8, color="darkred", weight="bold")
    ax.legend([Line2D([0], [0], color=c[3], lw=4) for c in CLASES], [c[2] for c in CLASES],
              loc="lower left", fontsize=8, title="Cota del bordo (msnm)")
    ax.set_xlim(bx[0], bx[2]); ax.set_ylim(bx[1], bx[3])
    ax.ticklabel_format(useOffset=False, style="plain")
    fig.tight_layout()
    fig.savefig(png, dpi=110)


if __name__ == "__main__":
    main(*sys.argv[1:4])
