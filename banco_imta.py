import sys
import numpy as np, rasterio, geopandas as gpd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LightSource
from matplotlib.patches import Rectangle
from rasterio.windows import from_bounds

mdt, gpkg, png = sys.argv[1:4]
BN = (464236.5909, 2220064.6431)      # nivelación 12-11-2026, 2033.97 INEGI
AR = (464236.99, 2220067.25)          # punto IMTA, Z 2026.44
C = ((BN[0] + AR[0]) / 2, (BN[1] + AR[1]) / 2)
bordo = gpd.read_file(gpkg, layer="bordo")


def leer(r, cx, cy, R, maxpx=1200):
    w = from_bounds(cx - R, cy - R, cx + R, cy + R, r.transform)
    f = max(1, int(w.width / maxpx))
    z = r.read(1, window=w, out_shape=(int(w.height / f), int(w.width / f))).astype(float)
    z[z < 1900] = np.nan
    return z, [cx - R, cx + R, cy - R, cy + R], 2 * R / z.shape[1]


def sombra(ax, z, ext, res, exag):
    hs = LightSource(315, 45).hillshade(np.nan_to_num(z, nan=np.nanmedian(z)), vert_exag=exag, dx=res, dy=res)
    ax.imshow(hs, cmap="gray", extent=ext)


def puntos(ax, s=9, txt=True):
    ax.plot(*BN, "o", ms=s, mfc="red", mec="w", mew=1.5, zorder=5)
    ax.plot(*AR, "o", ms=s, mfc="#1d74c9", mec="w", mew=1.5, zorder=5)
    if txt:
        ax.annotate("BN supervisión\n2033.97 INEGI · MDE 2024.98–2025.40", BN, xytext=(10, -22),
                    textcoords="offset points", fontsize=8, color="red", weight="bold",
                    bbox=dict(fc="white", ec="none", alpha=0.85, pad=1))
        ax.annotate("IMTA\nZ 2026.44 · MDE 2026.33–2026.44", AR, xytext=(10, 8),
                    textcoords="offset points", fontsize=8, color="#1d74c9", weight="bold",
                    bbox=dict(fc="white", ec="none", alpha=0.85, pad=1))


fig, axs = plt.subplots(1, 3, figsize=(20, 7.5), gridspec_kw={"width_ratios": [1.15, 1, 1.12]})
with rasterio.open(mdt) as r:
    # 1. general: bordos y banco
    b = bordo.total_bounds
    cx, cy = (min(b[0], BN[0]) + max(b[2], BN[0])) / 2, (min(b[1], BN[1]) + max(b[3], BN[1])) / 2
    R = max(max(b[2], BN[0]) - min(b[0], BN[0]), max(b[3], BN[1]) - min(b[1], BN[1])) / 2 + 80
    z, ext, res = leer(r, cx, cy, R)
    a = axs[0]
    sombra(a, z, ext, res, 3)
    bordo.plot(ax=a, color="#f2a900", lw=2)
    a.plot([], [], color="#f2a900", lw=2, label="Bordos Tres Culturas")
    puntos(a, 8, False)
    a.plot([], [], "o", mfc="red", mec="w", label="BN supervisión (nivelación 12-11-2026)")
    a.plot([], [], "o", mfc="#1d74c9", mec="w", label="IMTA")
    a.add_patch(Rectangle((C[0] - 30, C[1] - 30), 60, 60, fill=False, ec="red", lw=1.5))
    a.legend(loc="lower left", fontsize=8)
    a.set_title("Ubicación general", fontsize=11)

    # 2. intermedio 60 x 60 m
    z, ext, res = leer(r, *C, 30)
    a = axs[1]
    sombra(a, z, ext, res, 2)
    im = a.imshow(z, cmap="terrain", alpha=0.45, extent=ext, vmin=np.nanpercentile(z, 2), vmax=np.nanpercentile(z, 98))
    puntos(a, 8, False)
    a.add_patch(Rectangle((C[0] - 7, C[1] - 7), 14, 14, fill=False, ec="red", lw=1.5))
    a.set_title("Alrededores · 60 x 60 m", fontsize=11)
    plt.colorbar(im, ax=a, shrink=0.75, label="Cota MDE IMTA (msnm)")

    # 3. detalle 14 x 14 m con curvas
    z, ext, res = leer(r, *C, 7)
    a = axs[2]
    sombra(a, z, ext, res, 2)
    im = a.imshow(z, cmap="terrain", alpha=0.55, extent=ext, vmin=2024.8, vmax=2026.8)
    cs = a.contour(z, levels=np.arange(2024.8, 2026.9, 0.2), colors="k", linewidths=0.4,
                   extent=[ext[0], ext[1], ext[3], ext[2]], origin="upper")
    a.clabel(cs, fmt="%.1f", fontsize=7)
    a.annotate("", xy=AR, xytext=BN, arrowprops=dict(arrowstyle="<->", color="k", lw=1))
    a.text((BN[0] + AR[0]) / 2 - 0.3, (BN[1] + AR[1]) / 2, "2.6 m", ha="right", fontsize=8, weight="bold")
    puntos(a, 9, True)
    a.set_title("Detalle · 14 x 14 m, curvas cada 0.2 m", fontsize=11)
    plt.colorbar(im, ax=a, shrink=0.75, label="Cota MDE IMTA (msnm)")

for a in axs:
    a.ticklabel_format(useOffset=False, style="plain")
    a.tick_params(labelsize=7)
fig.suptitle("Banco de nivel IMTA en el MDE de Tres Culturas: BN supervisión (rojo) vs IMTA (azul) · EPSG:32614", fontsize=12)
fig.tight_layout()
fig.savefig(png, dpi=140)
