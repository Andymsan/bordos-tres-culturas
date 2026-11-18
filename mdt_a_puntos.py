import sys, os
import numpy as np, rasterio, laspy, ezdxf
from rasterio.enums import Resampling
from rasterio.windows import Window
from pyproj import CRS

Z_MIN = 1900                # valores menores son "sin dato"
BLOQUE = 250                # filas de salida por bloque
PUNTOS_DXF = 2_000_000      # máximo de puntos por archivo DXF


def main(mdt, out, paso="1"):
    paso = float(paso)
    os.makedirs(out, exist_ok=True)
    nombre = f"{out}/MDT_{paso:g}m"
    with rasterio.open(mdt) as r:
        f = paso / r.res[0]
        filas, cols = int(r.height / f), int(r.width / f)
        las = laspy.LasHeader(point_format=0, version="1.2")
        las.scales = [0.001] * 3
        las.offsets = [r.bounds.left, r.bounds.bottom, 1900]
        las.add_crs(CRS.from_wkt(r.crs.to_wkt()))
        dxf, n_dxf, k_dxf = None, 0, 0
        with laspy.open(f"{nombre}.las", mode="w", header=las) as wl, open(f"{nombre}.xyz", "w") as wx:
            for i0 in range(0, filas, BLOQUE):
                h = min(BLOQUE, filas - i0)
                win = Window(0, i0 * f, r.width, h * f)
                z = r.read(1, window=win, out_shape=(h, cols), resampling=Resampling.average, masked=True)
                ii, jj = np.nonzero(~np.ma.getmaskarray(z) & (z.filled(0) > Z_MIN))
                if not len(ii):
                    continue
                x = r.bounds.left + (jj + 0.5) * paso
                y = r.bounds.top - (i0 + ii + 0.5) * paso
                zz = z.data[ii, jj].astype("float64")
                p = laspy.ScaleAwarePointRecord.zeros(len(x), header=las)
                p.x, p.y, p.z = x, y, zz
                wl.write_points(p)
                np.savetxt(wx, np.column_stack([x, y, zz]), fmt="%.2f %.2f %.3f")
                for a, b, c in zip(x, y, zz):
                    if dxf is None or n_dxf >= PUNTOS_DXF:
                        if dxf is not None:
                            dxf.saveas(f"{nombre}_{k_dxf:02d}.dxf")
                        k_dxf += 1
                        dxf = ezdxf.new("R2010", units=6)
                        dxf.layers.add(f"MDT_{paso:g}m", color=8)
                        msp, n_dxf = dxf.modelspace(), 0
                    msp.add_point((a, b, c), dxfattribs={"layer": f"MDT_{paso:g}m"})
                    n_dxf += 1
                print(f"{min(i0 + h, filas)}/{filas} filas", flush=True)
        if dxf is not None:
            dxf.saveas(f"{nombre}_{k_dxf:02d}.dxf")


if __name__ == "__main__":
    main(*sys.argv[1:4])
