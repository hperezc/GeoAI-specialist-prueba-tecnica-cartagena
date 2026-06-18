"""
Funciones de visualización: rasterización y generación de mapas estáticos.
"""

import numpy as np
import geopandas as gpd
import rasterio
from rasterio import features
from rasterio.transform import from_bounds
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import LinearSegmentedColormap


def rasterizar_gdf(gdf, columna, resolucion_m=100, dtype="float32"):
    """
    Convierte una columna numérica de un GeoDataFrame en un raster regular.
    Asume CRS proyectado (en metros).
    """
    xmin, ymin, xmax, ymax = gdf.total_bounds
    ancho = int((xmax - xmin) / resolucion_m)
    alto = int((ymax - ymin) / resolucion_m)
    transform = from_bounds(xmin, ymin, xmax, ymax, ancho, alto)

    shapes = ((g, v) for g, v in zip(gdf.geometry, gdf[columna]))
    arr = features.rasterize(
        shapes=shapes,
        out_shape=(alto, ancho),
        transform=transform,
        fill=np.nan,
        dtype=dtype,
    )
    return arr, transform, gdf.crs


def guardar_geotiff(arr, transform, crs, path, nodata=np.nan):
    """Guarda un array 2D como GeoTIFF con CRS y transform."""
    with rasterio.open(
        path, "w",
        driver="GTiff",
        height=arr.shape[0], width=arr.shape[1],
        count=1, dtype=arr.dtype,
        crs=crs, transform=transform,
        nodata=nodata,
        compress="lzw",
    ) as dst:
        dst.write(arr, 1)


def colormap_probabilidad():
    """Colormap secuencial para probabilidad de asentamiento informal."""
    colors = ["#f7f4f9", "#e7d4e8", "#d4b9da", "#c994c7",
              "#df65b0", "#dd1c77", "#980043", "#67001f"]
    return LinearSegmentedColormap.from_list("informalidad", colors, N=256)


def colormap_clases():
    """Colormap discreto para las 4 clases de probabilidad."""
    return {
        "Baja": "#fde0dd",
        "Media": "#fa9fb5",
        "Alta": "#c51b8a",
        "Muy alta": "#7a0177",
    }
