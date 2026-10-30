import sys, numpy as np, rasterio, laspy
from rasterio.warp import reproject, Resampling

MDT, OUT = sys.argv[1], sys.argv[2]
RGB = sys.argv[3] if len(sys.argv) > 3 and sys.argv[3].endswith(".tif") else None
PASO = int(sys.argv[-1]) if sys.argv[-1].isdigit() else 1

with rasterio.open(MDT) as r:
    z = r.read(1).astype("float64")[::PASO, ::PASO]
    T = r.transform * rasterio.Affine.scale(PASO); crs = r.crs; shape = z.shape
    nd = r.nodata
ok = np.isfinite(z) & (z > 1900) & ((z != nd) if nd is not None else True)

filas, cols = np.nonzero(ok)
x, y = rasterio.transform.xy(T, filas, cols, offset="center")
x, y, zz = np.asarray(x), np.asarray(y), z[ok]

h = laspy.LasHeader(point_format=3 if RGB else 0, version="1.4")
h.scales = [0.01, 0.01, 0.01]; h.offsets = [x.min(), y.min(), zz.min()]
h.add_crs(crs)
las = laspy.LasData(h); las.x, las.y, las.z = x, y, zz

if RGB:  # color de la imagen satelital, remuestreada a la malla del MDT
    with rasterio.open(RGB) as s:
        rgb = np.zeros((3, *shape), dtype="float32")
        for b in range(3):
            reproject(rasterio.band(s, b + 1), rgb[b], dst_transform=T, dst_crs=crs, resampling=Resampling.bilinear)
    for b, dim in enumerate(["red", "green", "blue"]):
        v = rgb[b][ok]; v = (v - np.percentile(v, 2)) / (np.percentile(v, 98) - np.percentile(v, 2))
        setattr(las, dim, (np.clip(v, 0, 1) * 65535).astype("uint16"))

las.write(OUT)
print(f"{len(zz):,} puntos -> {OUT}  (z {zz.min():.2f}–{zz.max():.2f} msnm)")
