# Bordos Tres Culturas

## Perfiles

![Margen izquierda](resultados/perfil_margen_Izquierda.png)

![Margen derecha](resultados/perfil_margen_Derecha.png)

## Bordos

![Mapa de bordos](resultados/mapa_bordos.png)

## Árboles y edificios

![Árboles y edificios](resultados/mapa_obstaculos.png)

## Temporada por mes

![Temporada por mes](resultados/temporada_por_mes.png)

## Bordo libre por tramo

![Bordo libre por tramo](resultados/bordo_libre_por_tramo.png)

## Tablas

- [Puntos bajos](resultados/puntos_bajos.csv): tramos con bordo libre < 1 m sobre el NAME
- [Resumen por margen](resultados/resumen_por_margen.csv)
- [Temporada por mes](resultados/temporada_por_mes.csv)
- [Bordo libre por tramo](resultados/bordo_libre_por_tramo.csv)

## Archivos

| Archivo | Contenido |
|---|---|
| `datos/bordos.gpkg` | Eje por margen |
| `resultados/bordo_analisis.gpkg` | Bordo por cota, puntos bajos, bordos y obstáculos |
| `estilos/` | Estilos QGIS para el MDT y las capas |
| `gee_obstaculos.py` | Dosel (Meta), NDVI 2025 (Sentinel-2) y edificios (Open Buildings) desde Earth Engine |
| `bordo_analisis.py` | Perfil, frecuencias y puntos bajos; excluye árboles y edificios |
| `temporada_por_mes.py` | Tabla y figura mes × cota |
| `bordo_libre_por_tramo.py` | Bordo libre sobre el NAME del punto más bajo de cada tramo de 100 m |
| `mapa.py` | Mapa del bordo por cota |
| `mapa_obstaculos.py` | Mapa de árboles y edificios sobre y cerca del bordo |

## Uso

```
pip install -r requirements.txt
python temporada_por_mes.py niveles_endho.xlsx resultados
python gee_obstaculos.py datos/bordos.gpkg bordo datos <proyecto_gee>
python bordo_analisis.py MDT_27102025.tif niveles_endho.xlsx datos/bordos.gpkg bordo resultados datos/satelite.tif
python bordo_libre_por_tramo.py niveles_endho.xlsx resultados
python mapa.py MDT_27102025.tif resultados/bordo_analisis.gpkg resultados/mapa_bordos.png
python mapa_obstaculos.py MDT_27102025.tif resultados resultados/mapa_obstaculos.png
```

MDT: `MDT_27102025.tif` (EPSG:32614), modelo de elevación del IMTA. Niveles: registro diario de la presa Endhó 1995–2025.

## Datum

Las cotas del MDT (IMTA) y los niveles de la presa (Endhó) usan bancos de nivel distintos. Ligas topográficas:

| Referencia | Endhó | IMTA | INEGI |
|---|---|---|---|
| Cresta del vertedor | 2018.00 | | 2022.04 |
| Banco IMTA | | 2026.44 | 2033.97 |

INEGI = Endhó + 4.04 = IMTA + 7.53, por lo tanto **Endhó = IMTA + 3.49**. `bordo_analisis.py` suma `IMTA_A_ENDHO = 3.49` al MDT, así que todas las cotas de `resultados/` están en datum Endhó. `mdt_a_puntos.py` exporta el MDT sin ajuste (datum IMTA). La diferencia de 0.09 m entre la regleta y la cresta se desprecia por ahora.

Equivalencias (Endhó → MDE): cresta 2018.00 → 2014.51; nivel máximo registrado 2019.38 → 2015.89; NAME 2020.00 → 2016.51; NAME + 1 m 2021.00 → 2017.51.

## Clases y puntos bajos

El bordo se clasifica por **bordo libre sobre el NAME** (2020 msnm, datum Endhó) en pasos de 0.5 m. Un punto bajo es un tramo de al menos 2 m con bordo libre menor a `BORDO_LIBRE_MIN = 1.0` m (cota < 2021.0), medido en el perfil de detalle (20 m).
