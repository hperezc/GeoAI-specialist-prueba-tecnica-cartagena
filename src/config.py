"""
Configuración global del proyecto.
Centralizar aquí todas las constantes evita 'magic numbers' dispersos en los notebooks.
"""

from pathlib import Path

# ────────────────────────────────────────────────────────────────────────────
# Rutas del proyecto
# ────────────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
DATA_RAW = ROOT / "data" / "raw"
DATA_PROC = ROOT / "data" / "processed"
OUTPUTS = ROOT / "outputs"
OUTPUTS_MAPS = OUTPUTS / "maps"
OUTPUTS_RESULTS = OUTPUTS / "results"
DOCS = ROOT / "docs"

# Crear si no existen
for d in (DATA_RAW, DATA_PROC, OUTPUTS_MAPS, OUTPUTS_RESULTS, DOCS):
    d.mkdir(parents=True, exist_ok=True)

# ────────────────────────────────────────────────────────────────────────────
# Google Earth Engine
# ────────────────────────────────────────────────────────────────────────────
# Project ID registrado en https://console.cloud.google.com/earth-engine
# Si quien reproduce el flujo tiene otro project ID, basta con sustituir aquí.
GEE_PROJECT = "ee-hectorcperez21"

# ────────────────────────────────────────────────────────────────────────────
# Sistemas de referencia
# ────────────────────────────────────────────────────────────────────────────
# Cartagena cae en la zona UTM 18N (huso 18, hemisferio norte).
# EPSG:32618 = WGS 84 / UTM zone 18N. Apropiado para análisis local en metros.
CRS_TRABAJO = "EPSG:32618"
CRS_WGS = "EPSG:4326"

# ────────────────────────────────────────────────────────────────────────────
# Área de estudio
# ────────────────────────────────────────────────────────────────────────────
# Nombre para geocodificación vía OSM (usado solo para descarga de vías y edificios OSM)
CIUDAD_NOMBRE = "Cartagena de Indias, Bolívar, Colombia"

# Bounding box aproximado de Cartagena urbana (longitud, latitud) — fallback
CARTAGENA_BBOX_WGS = (-75.58, 10.28, -75.42, 10.46)  # (xmin, ymin, xmax, ymax)

# Ruta al shapefile del perímetro urbano oficial.
# Capa: MGN_URB_ZONA_URBANA del Marco Geoestadístico Nacional 2024 (DANE),
# descargada desde el geoportal Colombia en Mapas del IGAC
# (https://www.colombiaenmapas.gov.co), fuente oficial de información cartográfica del país.
# Esta fuente se prefiere sobre OSM porque delimita específicamente el suelo urbano oficial.
PERIMETRO_URBANO_SHP = (
    DATA_RAW / "cartagena_perimetro_urbano_dane" / "cartagena_perimetro_urbano_dane.shp"
)

# Código DIVIPOLA de Cartagena (Bolívar)
DIVIPOLA_CARTAGENA = "13001"

# ────────────────────────────────────────────────────────────────────────────
# Parámetros de adquisición de datos
# ────────────────────────────────────────────────────────────────────────────
# Ventana temporal de imágenes satelitales
FECHA_INICIO = "2024-01-01"
FECHA_FIN = "2024-12-31"

# Umbral de nubosidad para Sentinel-2
S2_CLOUD_PCT_MAX = 30

# ────────────────────────────────────────────────────────────────────────────
# Parámetros de la grilla de análisis
# ────────────────────────────────────────────────────────────────────────────
# Tamaño de celda en metros
TAMAÑO_CELDA_M = 100

# ────────────────────────────────────────────────────────────────────────────
# Parámetros del modelo
# ────────────────────────────────────────────────────────────────────────────
RANDOM_STATE = 42
N_ESTIMATORS = 200
TEST_SIZE = 0.30

# ────────────────────────────────────────────────────────────────────────────
# Shapefile de barrios de Cartagena
# ────────────────────────────────────────────────────────────────────────────
# Fuente: Cartagena Cómo Vamos (CCV) — ArcGIS Hub Open Data
# https://ccv-cgenacomovamos.opendata.arcgis.com/datasets/b9c35e8a5a364634aacaae0fc4168030_0
BARRIOS_SHP = (
    DATA_RAW.parent.parent
    / "data-colombia" / "Barrios_de_Cartagena" / "Barrios_de_Cartagena.shp"
)

# ────────────────────────────────────────────────────────────────────────────
# Etiquetas de barrios — nombres exactos del shapefile CCV
# ────────────────────────────────────────────────────────────────────────────
# Barrios formales consolidados (negativos del modelo).
# Mezcla deliberada de barrios formales "altos" (Bocagrande, Centro, Manga) y formales
# populares/medios consolidados (Blas de Lezo, Los Alpes, Daniel Lemaitre, etc.) para dar
# al modelo capacidad de distinguir la frontera entre informal y formal modesto.
BARRIOS_FORMALES = [
    # Centro amurallado + península turística
    "CENTRO", "GETSEMANI", "SAN DIEGO", "LA MATUNA",
    "BOCAGRANDE", "CASTILLOGRANDE", "EL LAGUITO",
    # Centro-norte residencial formal alto
    "MANGA", "PIE DE LA POPA", "PIE DEL CERRO",
    "EL CABRERO", "MARBELLA", "CRESPO",
    "ALTO BOSQUE",
    # Residencial formal medio
    "LOS CARACOLES", "LOS EJECUTIVOS", "CHIQUINQUIRA",
    "LOS ALPES", "LOS ANGELES", "LOS CERROS",
    "LOS CORALES", "LOS JARDINES",
    "LA CASTELLANA", "LA CAMPIÑA", "LA CAROLINA",
    "LA ESMERALDA I", "LA ESMERALDA II",
    # Formal popular consolidado (frontera con informal)
    "BLAS DE LEZO", "EL BOSQUE", "NUEVO BOSQUE",
    "LAS DELICIAS", "ESCALLON VILLA",
    "DANIEL LEMAITRE", "TORICES", "BUENOS AIRES",
    "AMBERES", "BRUSELAS", "SAN PEDRO",
    "ARMENIA", "SANTA MONICA",
]

# Barrios informales conocidos (positivos del modelo)
# Incluye zona norte/oriente (Olaya, Mandela, Pozón, Boston) y sectores informales del sur
BARRIOS_INFORMALES = [
    # Olaya Herrera y sub-barrios
    "OLAYA ST. CENTRAL", "OLAYA ST. LA MAGDALENA", "OLAYA ST. LA PUNTILLA",
    "OLAYA ST. PLAYA BLANCA", "OLAYA ST. PROGRESO", "OLAYA ST. RAFAEL NUÑEZ",
    "OLAYA ST. RICAURTE", "OLAYA ST. STELLA", "OLAYA ST. ZARABANDA",
    "OLAYA ST.11 DE NOVIEMBRE", "OLAYA VILLA OLIMPICA",
    # Otros informales norte/oriente
    "NELSON MANDELA", "EL POZON", "BOSTON", "SAN FRANCISCO",
    "LOMA FRESCA", "LO AMADOR", "FREDONIA",
    "POLICARPA", "JUAN XXIII",
    # Sur y suroriente
    "HENEQUEN", "LAS PALMERAS", "ALBORNOZ", "ARROZ BARATO",
    "VILLA BARRAZA", "VILLA FANNY", "VILLA RUBIA",
    "VILLA HERMOSA", "VILLA SANDRA",
    "NUEVA JERUSALEN", "NUEVO PARAISO", "NUEVO PORVENIR",
    "LAS GAVIOTAS",
]
