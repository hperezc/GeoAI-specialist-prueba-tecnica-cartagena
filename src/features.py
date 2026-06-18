"""
Funciones para construcción de variables (features) por celda de la grilla.
"""

import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
from rasterio.warp import reproject, Resampling
from shapely.geometry import Point


# ────────────────────────────────────────────────────────────────────────────
# Índices espectrales
# ────────────────────────────────────────────────────────────────────────────

def calcular_ndvi(nir, red):
    """Normalized Difference Vegetation Index. Alto => vegetación."""
    return (nir - red) / (nir + red + 1e-10)


def calcular_ndbi(swir, nir):
    """Normalized Difference Built-up Index. Alto => construido."""
    return (swir - nir) / (swir + nir + 1e-10)


def calcular_ndwi(green, nir):
    """Normalized Difference Water Index. Alto => agua."""
    return (green - nir) / (green + nir + 1e-10)


def calcular_bsi(swir1, red, nir, blue):
    """Bare Soil Index. Alto => suelo desnudo."""
    return ((swir1 + red) - (nir + blue)) / ((swir1 + red) + (nir + blue) + 1e-10)


# ────────────────────────────────────────────────────────────────────────────
# Texturas GLCM (Gray-Level Co-occurrence Matrix)
# ────────────────────────────────────────────────────────────────────────────

def textura_glcm(banda, distances=(1,), angles=(0,), levels=32):
    """
    Calcula descriptores GLCM (contraste, homogeneidad, energía).
    `banda` es un array 2D escalado a enteros 0..levels-1.
    """
    from skimage.feature import graycomatrix, graycoprops

    banda_q = np.clip((banda - banda.min()) / (banda.max() - banda.min() + 1e-10), 0, 1)
    banda_q = (banda_q * (levels - 1)).astype(np.uint8)

    glcm = graycomatrix(banda_q, distances=distances, angles=angles,
                         levels=levels, symmetric=True, normed=True)
    return {
        "contrast": graycoprops(glcm, "contrast").mean(),
        "homogeneity": graycoprops(glcm, "homogeneity").mean(),
        "energy": graycoprops(glcm, "energy").mean(),
    }


# ────────────────────────────────────────────────────────────────────────────
# Variables topográficas
# ────────────────────────────────────────────────────────────────────────────

def pendiente_desde_dem(dem_array, cellsize=30):
    """
    Calcula pendiente en grados desde un array DEM usando el método de Horn.
    """
    dy, dx = np.gradient(dem_array, cellsize)
    slope_rad = np.arctan(np.sqrt(dx**2 + dy**2))
    return np.degrees(slope_rad)


def tpi_desde_dem(dem_array, ventana=5):
    """
    Topographic Position Index: diferencia entre cada celda y la media de su vecindad.
    Positivo => cresta. Negativo => valle.
    """
    from scipy.ndimage import uniform_filter

    media_local = uniform_filter(dem_array, size=ventana, mode="nearest")
    return dem_array - media_local


# ────────────────────────────────────────────────────────────────────────────
# Densidad y métricas OSM
# ────────────────────────────────────────────────────────────────────────────

def densidad_vias_por_celda(grilla, vias):
    """
    Calcula longitud total de vías (km) por celda de la grilla.
    Ambos GeoDataFrames deben estar en el mismo CRS proyectado (metros).
    """
    grilla = grilla.copy()
    vias = vias.copy()
    # Asegurar CRS común
    if vias.crs != grilla.crs:
        vias = vias.to_crs(grilla.crs)

    # Intersectar
    inter = gpd.overlay(vias[["geometry"]], grilla[["cell_id", "geometry"]],
                         how="intersection", keep_geom_type=False)
    inter["long_m"] = inter.geometry.length
    densidad = inter.groupby("cell_id")["long_m"].sum().rename("vias_long_m")
    grilla = grilla.merge(densidad, on="cell_id", how="left")
    grilla["vias_long_m"] = grilla["vias_long_m"].fillna(0)
    return grilla


def metricas_edificios_por_celda(grilla, edificios):
    """
    Por celda: número de edificios, área total, área media, varianza del área,
    compacidad media (4*pi*area / perimetro^2).
    """
    grilla = grilla.copy()
    edificios = edificios.copy()
    if edificios.crs != grilla.crs:
        edificios = edificios.to_crs(grilla.crs)

    edificios["area_m2"] = edificios.geometry.area
    edificios["perim_m"] = edificios.geometry.length
    edificios["compacidad"] = (4 * np.pi * edificios["area_m2"]) / (edificios["perim_m"] ** 2 + 1e-10)
    edificios["centroide"] = edificios.geometry.centroid

    # Joint spatial: asignar cada edificio a la celda donde está su centroide
    cents = gpd.GeoDataFrame(
        edificios[["area_m2", "perim_m", "compacidad"]],
        geometry=edificios["centroide"],
        crs=edificios.crs,
    )
    joined = gpd.sjoin(cents, grilla[["cell_id", "geometry"]],
                       how="left", predicate="within")

    agg = joined.groupby("cell_id").agg(
        n_edificios=("area_m2", "count"),
        area_total_m2=("area_m2", "sum"),
        area_media_m2=("area_m2", "mean"),
        area_std_m2=("area_m2", "std"),
        compacidad_media=("compacidad", "mean"),
    )

    grilla = grilla.merge(agg, on="cell_id", how="left")
    for col in ["n_edificios", "area_total_m2", "area_media_m2", "area_std_m2", "compacidad_media"]:
        grilla[col] = grilla[col].fillna(0)
    return grilla


def distancia_a_vias_principales(grilla, vias):
    """
    Para cada celda, distancia desde su centroide a la vía 'primary' o 'trunk' más cercana.
    """
    grilla = grilla.copy()
    vias = vias.copy()
    if vias.crs != grilla.crs:
        vias = vias.to_crs(grilla.crs)

    # Filtrar vías principales
    if "highway" in vias.columns:
        principales = vias[vias["highway"].isin(["primary", "trunk", "secondary", "motorway"])]
    else:
        principales = vias

    if principales.empty:
        grilla["dist_via_principal_m"] = np.nan
        return grilla

    # Unir geometría
    union = principales.geometry.unary_union
    centroides = grilla.geometry.centroid
    grilla["dist_via_principal_m"] = centroides.distance(union)
    return grilla


# ────────────────────────────────────────────────────────────────────────────
# Zonal stats genérica con rasterio
# ────────────────────────────────────────────────────────────────────────────

def zonal_stats_grilla(grilla, raster_path, banda=1, stats=("mean", "std")):
    """
    Calcula estadísticas zonales por celda usando rasterio (sin dependencia de rasterstats).
    Para mantener simple, hace muestreo en el centroide en lugar de promedio por celda.
    Esto es razonable cuando la resolución del raster es ≤ tamaño de la celda.
    """
    grilla = grilla.copy()
    with rasterio.open(raster_path) as src:
        # Reproyectar centroides al CRS del raster
        centroides = grilla.geometry.centroid
        if src.crs != grilla.crs:
            centroides_proj = gpd.GeoSeries(centroides, crs=grilla.crs).to_crs(src.crs)
        else:
            centroides_proj = centroides

        coords = [(p.x, p.y) for p in centroides_proj]
        valores = list(src.sample(coords, indexes=banda))
        grilla[f"valor"] = [v[0] if len(v) > 0 else np.nan for v in valores]
    return grilla


def zonal_stats_multibanda(grilla, raster_path, nombres_bandas):
    """
    Igual que zonal_stats_grilla pero para todas las bandas de un raster multibanda.
    Devuelve la grilla con una columna por banda.
    """
    grilla = grilla.copy()
    with rasterio.open(raster_path) as src:
        n_bandas = src.count
        if len(nombres_bandas) != n_bandas:
            raise ValueError(f"Esperaba {n_bandas} nombres, recibí {len(nombres_bandas)}")

        centroides = grilla.geometry.centroid
        if src.crs != grilla.crs:
            centroides_proj = gpd.GeoSeries(centroides, crs=grilla.crs).to_crs(src.crs)
        else:
            centroides_proj = centroides
        coords = [(p.x, p.y) for p in centroides_proj]

        for i, nombre in enumerate(nombres_bandas, start=1):
            valores = list(src.sample(coords, indexes=i))
            grilla[nombre] = [v[0] if len(v) > 0 else np.nan for v in valores]
    return grilla
