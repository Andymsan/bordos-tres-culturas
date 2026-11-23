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

## Datum

Las cotas del MDT (IMTA) y los niveles de la presa (Endhó) usan bancos de nivel distintos:

| Referencia | Endhó | IMTA | INEGI |
|---|---|---|---|
| Cresta del vertedor | 2018.00 | | 2022.04 |
| Banco IMTA | | 2026.44 | 2033.97 |

INEGI = Endhó + 4.04 = IMTA + 7.53, por lo tanto **Endhó = IMTA + 3.49**.

Equivalencias (Endhó → MDE): cresta 2018.00 → 2014.51; nivel máximo registrado 2019.38 → 2015.89; NAME 2020.00 → 2016.51; NAME + 1 m 2021.00 → 2017.51.

## Revisión del banco de nivel IMTA

![Banco de nivel IMTA en el MDE](resultados/banco_imta_mde.png)

Punto azul: coincide, hay una diferencia de .11. 
Punto rojo (supervisión): está 2.6 m al sur y el MDE baja a 2025.40 por el canal 
Con ese punto sería 4.53 en vez de 3.49.

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
| `banco_imta.py` | Mapa del banco de nivel IMTA en el MDE: punto medido vs punto de Ariel |

## Uso

```
pip install -r requirements.txt
python temporada_por_mes.py niveles_endho.xlsx resultados
python gee_obstaculos.py datos/bordos.gpkg bordo datos <proyecto_gee>
python bordo_analisis.py MDT_27102025.tif niveles_endho.xlsx datos/bordos.gpkg bordo resultados datos/satelite.tif
python bordo_libre_por_tramo.py niveles_endho.xlsx resultados
python mapa.py MDT_27102025.tif resultados/bordo_analisis.gpkg resultados/mapa_bordos.png
python mapa_obstaculos.py MDT_27102025.tif resultados resultados/mapa_obstaculos.png
python banco_imta.py MDT_27102025.tif resultados/bordo_analisis.gpkg resultados/banco_imta_mde.png
```

MDT: `MDT_27102025.tif` (EPSG:32614), modelo de elevación del IMTA. Niveles: registro diario de la presa Endhó 1995–2025.



