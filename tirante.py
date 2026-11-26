import sys, os
import numpy as np, rasterio, geopandas as gpd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LightSource
from rasterio.enums import Resampling
from bordo_analisis import IMTA_A_ENDHO

# Niveles de la presa en datum Endhó; se pasan al MDE restando IMTA_A_ENDHO
NIVELES = [("NAMO", "cresta del vertedor", 2018.00), ("Nivel máximo", "9 septiembre 2021", 2019.38),
           ("NAME", "2 m sobre el vertedor", 2020.00)]
PASO = 1.0                      # m, resolución de salida
VMAX = 4.0                      # m, tope de la escala de color


def main(mdt, gpkg, out):
    os.makedirs(out, exist_ok=True)
    with rasterio.open(mdt) as r:
        f = PASO / r.res[0]
        h, w = int(r.height / f), int(r.width / f)
        z = r.read(1, out_shape=(h, w), resampling=Resampling.average).astype("float32")
        T = r.transform * r.transform.scale(r.width / w, r.height / h)
        perfil = r.profile
    z[z < 1900] = np.nan
    perfil.update(width=w, height=h, transform=T, dtype="float32", nodata=-9999, count=1,
                  compress="deflate", tiled=True, blockxsize=256, blockysize=256, BIGTIFF="IF_SAFER")
    ext = [T.c, T.c + T.a * w, T.f + T.e * h, T.f]
    bordo = gpd.read_file(gpkg, layer="bordo")
    hs = LightSource(315, 45).hillshade(np.nan_to_num(z, nan=np.nanmedian(z)), vert_exag=3, dx=PASO, dy=PASO)

    fig, axs = plt.subplots(1, 3, figsize=(18, 12), layout="constrained")
    filas = []
    for ax, (nombre, desc, nivel) in zip(axs, NIVELES):
        nivel_mde = nivel - IMTA_A_ENDHO
        t = np.where(np.isfinite(z), np.maximum(0, nivel_mde - z), np.nan).astype("float32")
        archivo = f"{out}/tirante_{nombre.replace(' ', '_').replace('á', 'a')}.tif"
        with rasterio.open(archivo, "w", **perfil) as dst:
            dst.write(np.where(np.isfinite(t), t, -9999).astype("float32"), 1)
        moj = t > 0
        filas.append((nombre, nivel, nivel_mde, moj.sum() * PASO ** 2 / 1e4, float(np.nanmax(t)),
                      float(np.nanmedian(t[moj])) if moj.any() else 0))
        ax.imshow(hs, cmap="gray", extent=ext)
        im = ax.imshow(np.ma.masked_less_equal(t, 0), cmap="Blues", vmin=0, vmax=VMAX, extent=ext)
        bordo.plot(ax=ax, color="#e8590c", lw=0.8)
        ax.set_title(f"{nombre} ({desc})\n{nivel:.2f} Endhó · {nivel_mde:.2f} MDE IMTA", fontsize=11)
        ax.set_xticks([]); ax.set_yticks([])
    cb = fig.colorbar(im, ax=axs.tolist(), orientation="horizontal", shrink=0.5, extend="max")
    cb.set_label("Tirante (m) = nivel de la presa − topografía IMTA")
    fig.suptitle("Tirante de agua con la presa Endhó a distintos niveles · Tres Culturas", fontsize=13)
    fig.savefig(f"{out}/tirante.png", dpi=130)
    for n, nv, nm, ha, tmax, tmed in filas:
        print(f"{n}: {nv:.2f} Endhó / {nm:.2f} MDE · {ha:.1f} ha con agua · tirante máx {tmax:.2f} m · mediana {tmed:.2f} m")
    print(f"MDE mínimo (posible superficie del agua del río al volar): {np.nanmin(z):.2f} MDE = {np.nanmin(z) + IMTA_A_ENDHO:.2f} Endhó")


if __name__ == "__main__":
    main(*sys.argv[1:4])
