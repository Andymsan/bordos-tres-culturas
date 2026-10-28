import sys, os, math, statistics
import numpy as np, pandas as pd, rasterio, geopandas as gpd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.colors import ListedColormap, BoundaryNorm
from rasterio.windows import from_bounds
from rasterio.warp import reproject, Resampling
from rasterio.features import shapes
from scipy import ndimage as ndi
from scipy.signal import savgol_filter
from skimage.morphology import remove_small_objects
from shapely.geometry import LineString, Point, shape

SEMIANCHO, PASO = 2.0, 0.5          # m
VENTANA_PERFIL = (121, 201)         # muestras: mediana 60 m + Savitzky-Golay 100 m, perfil del bordo
VENTANA_DETALLE = (41, 61)          # muestras: mediana 20 m + Savitzky-Golay 30 m, puntos bajos angostos
COTA_ALERTA = 2018.4                # msnm
LONG_MIN_BAJO = 2.0                 # m
Y_GRAFICA = (2013.0, 2023.0)        # msnm, eje vertical fijo
TAMANO_GRAFICA = (30, 4.5)          # pulgadas; más ancho = menos exageración vertical
PASO_GRAFICA = 2.0                  # m, espaciado del máximo de la franja en la gráfica
Z_ESTRUCTURA = 2022.0               # puentes, edificios y árboles se ignoran
INICIO_RIO = (463860, 2218660)      # aguas arriba; el perfil empieza en el extremo más cercano
SALIENTE = 1.0                      # m sobre la mediana del MDT en 5 m: algo sobresale
NDVI_ARBOL = 0.4                    # Sentinel-2
ALTURA_ARBOL = 2.0                  # m, dosel de Meta
OBSTACULO = {0: "no", 1: "árbol", 2: "edificio"}
MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
CLASES = [  # (desde, hasta, etiqueta, color viridis)
    (1990.0, 2016.0, "< 2016 · > 57% del tiempo", "#440154"),
    (2016.0, 2017.0, "2016–2017 · 46–57%", "#443983"),
    (2017.0, 2018.0, "2017–2018 · 23–46%", "#31688e"),
    (2018.0, 2018.4, "2018–2018.4 · 3–23%", "#21918c"),
    (2018.4, 2019.0, "2018.4–2019 · < 3%", "#35b779"),
    (2019.0, 2020.0, "2019–2020 · < 0.03%", "#90d743"),
    (2020.0, 2100.0, "≥ 2020 · NAME", "#fde725"),
]


def clase_de(z):
    for a, b, etiqueta, _ in CLASES:
        if a <= z < b:
            return etiqueta
    return CLASES[-1][2]


def mediana_movil(valores, n):
    m = n // 2
    out = []
    for i in range(len(valores)):
        v = [x for x in valores[max(0, i - m): i + m + 1] if x is not None]
        out.append(statistics.median(v) if v else None)
    return out


def suavizar(valores, n):
    v = pd.Series(valores, dtype="float64")
    ok = v.notna()
    if ok.sum() < n:
        return valores
    s = savgol_filter(v.interpolate(limit_direction="both"), n, 2)
    return [float(a) if b else None for a, b in zip(s, ok)]


def tramos_bajos(dist, z, cota, long_min):
    res, ini = [], None
    for i, v in enumerate(z + [None]):
        bajo = v is not None and v < cota
        if bajo and ini is None:
            ini = i
        elif not bajo and ini is not None:
            fin = i - 1
            if dist[fin] - dist[ini] >= long_min:
                k = min(range(ini, fin + 1), key=lambda j: z[j])
                res.append({"largo": dist[fin] - dist[ini], "i_min": k, "z_min": z[k]})
            ini = None
    return res


def graficar(titulo, dist, z_crudo, z_filt, bajos, ruta):
    plt.rcParams.update({"font.size": 15})
    fig, ax = plt.subplots(figsize=TAMANO_GRAFICA)
    k = max(1, int(PASO_GRAFICA / PASO))
    crudo = pd.Series([v if v is not None else np.nan for v in z_crudo]).groupby(np.arange(len(dist)) // k).max()
    ax.plot(dist[::k][:len(crudo)], crudo, color="#dddddd", lw=0.8, label="máximo de la franja")
    pts = [(d, v) for d, v in zip(dist, z_filt) if v is not None]
    segs = [[pts[i], pts[i + 1]] for i in range(len(pts) - 1)]
    limites = [c[0] for c in CLASES] + [CLASES[-1][1]]
    lc = LineCollection(segs, cmap=ListedColormap([c[3] for c in CLASES]),
                        norm=BoundaryNorm(limites, len(CLASES)), linewidths=4)
    lc.set_array([(a[1] + b[1]) / 2 for a, b in segs])
    ax.add_collection(lc)
    for cota, txt in [(2016, "2016"), (2018, "2018 · cresta del vertedor"), (2020, "2020 · NAME")]:
        ax.axhline(cota, ls="--", lw=0.8, color="#555")
        ax.text(dist[-1], cota + 0.05, txt, ha="right", va="bottom", fontsize=13, color="#333")
    ax.set_ylim(*Y_GRAFICA)
    ax.set_xlim(dist[0], dist[-1])
    ax.set_xlabel("Distancia a lo largo del bordo (m)")
    ax.set_ylabel("Cota del bordo (msnm)")
    ax.set_title(titulo)
    ax.grid(alpha=0.3)
    if bajos:
        ax.scatter([d for d, _, _ in bajos], [v for _, v, _ in bajos], marker="v", s=80, c="red", edgecolors="k", zorder=5,
                   label="punto bajo (detalle 20 m)")
        for d, v, largo in bajos:
            ax.annotate(f"{v:.2f}\n{largo:.0f} m", (d, v), xytext=(0, -10), textcoords="offset points",
                        ha="center", va="top", fontsize=12, color="darkred")
    ax.legend(loc="upper left", fontsize=13)
    fig.tight_layout()
    bb = ax.get_window_extent().transformed(fig.dpi_scale_trans.inverted())
    ex = ((dist[-1] - dist[0]) / bb.width) / ((Y_GRAFICA[1] - Y_GRAFICA[0]) / bb.height)
    ax.text(0.99, 0.98, f"Escala vertical exagerada ×{ex:.0f}", transform=ax.transAxes, ha="right", va="top",
            fontsize=13, color="#555", style="italic")
    fig.savefig(ruta, dpi=150)
    plt.close(fig)


def main(mdt, niveles, gpkg, capa, out, satelite=None):
    os.makedirs(out, exist_ok=True)
    lineas = gpd.read_file(gpkg, layer=capa)
    b = lineas.total_bounds
    with rasterio.open(mdt) as r:
        lineas = lineas.to_crs(r.crs)
        w = from_bounds(b[0] - 30, b[1] - 30, b[2] + 30, b[3] + 30, r.transform)
        z = r.read(1, window=w).astype("float64")
        z[z < 1900] = np.nan
        T, crs = r.window_transform(w), r.crs
    px = T.a
    valid = ~np.isnan(z)
    obst = np.zeros(z.shape, "uint8")
    if satelite:
        dosel, ndvi, edif = (np.zeros(z.shape, "float32") for _ in range(3))
        with rasterio.open(satelite) as o:
            for banda, dst in zip((1, 2, 3), (dosel, ndvi, edif)):
                reproject(o.read(banda).astype("float32"), dst, src_transform=o.transform, src_crs=o.crs,
                          dst_transform=T, dst_crs=crs, resampling=Resampling.nearest)
        relleno = np.where(valid, z, np.nanmedian(z))
        f = max(1, int(1 / px))
        h, w_ = (s // f * f for s in z.shape)
        grueso = relleno[:h, :w_].reshape(h // f, f, w_ // f, f).mean(axis=(1, 3))
        fondo = np.repeat(np.repeat(ndi.median_filter(grueso, int(5 / (px * f)) | 1), f, 0), f, 1)
        fondo = np.pad(fondo, ((0, z.shape[0] - h), (0, z.shape[1] - w_)), mode="edge")
        saliente = valid & (z - fondo > SALIENTE)
        arbol = (ndvi / 100 >= NDVI_ARBOL) & (saliente | (dosel >= ALTURA_ARBOL))
        obst[ndi.binary_dilation(arbol, iterations=int(1 / px))] = 1
        obst[edif > 0] = 2
    zf = np.where(valid & (obst == 0), z, -1e9)

    def rc(x, y):
        return int((T.f - y) / px), int((x - T.c) / px)

    k = int(10 / px) * 2 + 1
    media = ndi.uniform_filter(np.where(valid, z, 0), k) / np.maximum(ndi.uniform_filter(valid.astype("float32"), k), 1e-6)
    cresta = valid & (z - media > 0.3) & (z > 2015) & (z < Z_ESTRUCTURA)
    cresta = remove_small_objects(ndi.binary_closing(cresta, iterations=2), int(10 / px ** 2))
    cerca_cresta = ndi.binary_dilation(cresta, iterations=int(1.5 / px))

    def zmax(x, y, rad=0.3):
        r_, c_ = rc(x, y)
        n_ = max(1, int(rad / px))
        v = zf[max(0, r_ - n_): r_ + n_ + 1, max(0, c_ - n_): c_ + n_ + 1]
        v = v[(v > 0) & (v < Z_ESTRUCTURA)]
        return float(v.max()) if v.size else None

    def en_cresta(x, y):
        r_, c_ = rc(x, y)
        return bool(0 <= r_ < z.shape[0] and 0 <= c_ < z.shape[1] and cerca_cresta[r_, c_])

    def obstaculo(x, y):
        r_, c_ = rc(x, y)
        return OBSTACULO[int(obst[r_, c_])] if 0 <= r_ < z.shape[0] and 0 <= c_ < z.shape[1] else "no"

    nv = pd.read_excel(niveles, sheet_name="Gráfica Nivel Endhó", usecols=[1, 2])
    nv.columns = ["fecha", "nivel"]
    nv = nv.dropna()
    nv = nv[(nv.nivel > 1990) & (nv.nivel < 2030)]
    nv["mes"] = pd.to_datetime(nv.fecha).dt.month
    niv = np.sort(nv.nivel.values)
    niv_m = {m: np.sort(nv[nv.mes == m].nivel.values) for m in range(1, 13)}

    def pct(s, v):
        return 100 * (len(s) - np.searchsorted(s, v, side="right")) / len(s)

    def meses(v):
        ms = [MESES[m - 1] for m in range(1, 13) if pct(niv_m[m], v) >= 50]
        return ", ".join(ms) if ms else "ninguno"

    segs, bajos, resumen = [], [], []
    for j, f in lineas.iterrows():
        lado = str(f.get("margen") or f"linea_{j}")
        geoms = list(f.geometry.geoms) if f.geometry.geom_type.startswith("Multi") else [f.geometry]
        ln = LineString([c for g in geoms for c in g.coords])
        if Point(ln.coords[-1]).distance(Point(INICIO_RIO)) < Point(ln.coords[0]).distance(Point(INICIO_RIO)):
            ln = LineString(list(ln.coords)[::-1])

        dist, pts, zc, oc, ob = [], [], [], [], []
        for d in np.arange(0, ln.length, PASO):
            p = ln.interpolate(d)
            q, o = ln.interpolate(min(d + 1, ln.length)), ln.interpolate(max(d - 1, 0))
            tx, ty = q.x - o.x, q.y - o.y
            n_ = math.hypot(tx, ty) or 1
            nx, ny = -ty / n_, tx / n_
            vals = [zmax(p.x + s * nx, p.y + s * ny) for s in np.arange(-SEMIANCHO, SEMIANCHO + 0.01, PASO)]
            vals = [v for v in vals if v is not None]
            dist.append(d); pts.append(p); zc.append(max(vals) if vals else None); oc.append(en_cresta(p.x, p.y)); ob.append(obstaculo(p.x, p.y))
        zm = suavizar(mediana_movil(zc, VENTANA_PERFIL[0]), VENTANA_PERFIL[1])
        zd = suavizar(mediana_movil(zc, VENTANA_DETALLE[0]), VENTANA_DETALLE[1])
        marcas = []

        for i in range(len(pts) - 1):
            if zm[i] is None:
                continue
            v = zm[i]
            fr = pct(niv, v)
            segs.append({"margen": lado, "dist_m": round(dist[i], 1), "z_bordo": round(v, 2),
                         "z_cruda": round(zc[i], 2) if zc[i] is not None else None, "clase": clase_de(v),
                         "frec_pct": round(fr, 2), "dias_anio": round(fr * 3.65, 1), "meses_50pct": meses(v),
                         "sobre_cresta": "sí" if oc[i] else "no", "obstaculo": ob[i],
                         "geometry": LineString([pts[i], pts[i + 1]])})
        for t in tramos_bajos(dist, zd, COTA_ALERTA, LONG_MIN_BAJO):
            i, v = t["i_min"], t["z_min"]
            fr = pct(niv, v)
            marcas.append((dist[i], v, t["largo"]))
            bajos.append({"margen": lado, "dist_m": round(dist[i], 1), "z_min": round(v, 2), "largo_m": round(t["largo"], 1),
                          "frec_pct": round(fr, 1), "dias_anio": round(fr * 3.65), "meses_50pct": meses(v),
                          "sobre_cresta": "sí" if oc[i] else "no", "obstaculo": ob[i],
                          **{m: round(pct(niv_m[n + 1], v), 1) for n, m in enumerate(MESES)}, "geometry": pts[i]})

        zs = np.array([v for v in zm if v is not None])
        resumen.append({"margen": lado, "largo_m": round(ln.length), "z_min": round(zs.min(), 2),
                        "z_mediana": round(float(np.median(zs)), 2), "z_max": round(zs.max(), 2),
                        "m_bajo_2016": int((zs < 2016).sum() * PASO),
                        "m_2016_2017": int(((zs >= 2016) & (zs < 2017)).sum() * PASO),
                        "m_2017_2018": int(((zs >= 2017) & (zs < 2018)).sum() * PASO),
                        "m_2018_2018_4": int(((zs >= 2018) & (zs < 2018.4)).sum() * PASO),
                        "pct_sobre_cresta": round(100 * np.mean(oc)),
                        "m_arbol": int(ob.count("árbol") * PASO), "m_edificio": int(ob.count("edificio") * PASO), "geometry": ln})
        graficar(f"Perfil del bordo · margen {lado.lower()}", dist, zc, zm, marcas, f"{out}/perfil_margen_{lado}.png")
        pd.DataFrame({"dist_m": dist, "x": [p.x for p in pts], "y": [p.y for p in pts], "z_cruda": zc, "z_bordo": zm, "z_detalle": zd,
                      "dias_anio": [round(pct(niv, v) * 3.65, 1) if v is not None else None for v in zm],
                      "sobre_cresta": oc, "obstaculo": ob}).round(2).to_csv(f"{out}/perfil_margen_{lado}.csv", index=False, encoding="utf-8-sig")

    g = f"{out}/bordo_analisis.gpkg"
    if os.path.exists(g):
        os.remove(g)
    gpd.GeoDataFrame(resumen, crs=crs).to_file(g, layer="bordo", driver="GPKG")
    gpd.GeoDataFrame(segs, crs=crs).to_file(g, layer="bordo_por_cota", driver="GPKG")
    B = gpd.GeoDataFrame(bajos, crs=crs).sort_values("z_min")
    B.insert(0, "id", range(1, len(B) + 1))
    B.to_file(g, layer="puntos_bajos", driver="GPKG")
    if obst.any():
        franja = lineas.buffer(SEMIANCHO + 1).union_all()
        ob_geo = [(shape(p), OBSTACULO[int(v)]) for p, v in shapes(obst, mask=obst > 0, transform=T)]
        O = gpd.GeoDataFrame({"tipo": [t for _, t in ob_geo]}, geometry=[p for p, _ in ob_geo], crs=crs)
        O = O[O.intersects(lineas.buffer(40).union_all())].copy()
        O["sobre_bordo"] = np.where(O.intersects(franja), "sí", "no")
        O["area_m2"] = O.area.round(1)
        O.to_file(g, layer="obstaculos", driver="GPKG")
    B.drop(columns="geometry").assign(x=B.geometry.x.round(1), y=B.geometry.y.round(1)).to_csv(
        f"{out}/puntos_bajos.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(resumen).drop(columns="geometry").to_csv(f"{out}/resumen_por_margen.csv", index=False, encoding="utf-8-sig")


if __name__ == "__main__":
    main(*sys.argv[1:7])
