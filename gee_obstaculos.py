import sys, os, urllib.request
import ee

PERIODO = ("2025-01-01", "2025-10-27")
NUBES_MAX = 20              # % por escena
CONFIANZA_EDIFICIO = 0.7
ZONA = 40                   # m alrededor de las líneas
RESOLUCION = 1              # m
CRS = "EPSG:32614"


def main(gpkg, capa, out, proyecto):
    import geopandas as gpd
    os.makedirs(out, exist_ok=True)
    ee.Initialize(project=proyecto)
    x0, y0, x1, y1 = gpd.read_file(gpkg, layer=capa).to_crs(CRS).buffer(ZONA).total_bounds
    region = ee.Geometry.Rectangle([x0, y0, x1, y1], ee.Projection(CRS), False)

    dosel = ee.ImageCollection("projects/meta-forest-monitoring-okw37/assets/CanopyHeight").mosaic().rename("dosel_m")
    s2 = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED").filterBounds(region).filterDate(*PERIODO)
          .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", NUBES_MAX)))
    ndvi = (s2.map(lambda i: i.normalizedDifference(["B8", "B4"])).median()
            .setDefaultProjection(s2.first().select("B8").projection()).resample("bilinear").rename("ndvi"))
    edificios = (ee.FeatureCollection("GOOGLE/Research/open-buildings/v3/polygons")
                 .filterBounds(region).filter(ee.Filter.gte("confidence", CONFIANZA_EDIFICIO)))
    edif = ee.Image(0).paint(edificios, 1).rename("edificio")

    capas = ee.Image.cat([dosel.unmask(0), ndvi.multiply(100), edif]).toInt16()
    url = capas.getDownloadURL({"region": region, "crs": CRS, "scale": RESOLUCION, "format": "GEO_TIFF"})
    urllib.request.urlretrieve(url, f"{out}/satelite.tif")
    print(f"Sentinel-2: {s2.size().getInfo()} escenas · edificios: {edificios.size().getInfo()}")


if __name__ == "__main__":
    main(*sys.argv[1:5])
