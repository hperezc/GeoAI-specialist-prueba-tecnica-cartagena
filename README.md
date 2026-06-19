# Identificación de Asentamientos Informales en Cartagena de Indias mediante IA Geoespacial

**Prueba técnica — Especialista en Geoprocesamiento e IA para Soluciones Urbanas**
**ONU-Hábitat, HUB Países Andinos, Bogotá (Colombia)**

Autor: Héctor Camilo Pérez Contreras
Fecha: Junio 2026

---

## 1. Resumen del proyecto

Este repositorio contiene el flujo de trabajo completo para identificar áreas con probabilidad de corresponder a asentamientos informales dentro del perímetro urbano de Cartagena de Indias, mediante la integración de imágenes satelitales abiertas, datos geoespaciales auxiliares (OpenStreetMap, GHS-BUILT, WorldPop, VIIRS, Copernicus DEM) y técnicas de aprendizaje automático supervisado (Random Forest), con un enfoque explícito de *trust by design* y *human-in-the-loop*.

El producto final es un mapa de probabilidad clasificada (4 niveles) entregado en formatos GeoTIFF y GeoPackage, junto con la nota técnica que documenta enfoque, justificación, limitaciones, sesgos y recomendaciones de escalamiento.

## 2. Estructura del repositorio

```
prueba-tecnica-cartagena/
├── README.md                      # Este archivo
├── requirements.txt               # Dependencias Python
├── .gitignore                     # Archivos excluidos del control de versión
├── data/
│   ├── raw/                       # Datos descargados (no versionados)
│   └── processed/                 # Datos intermedios procesados
├── notebooks/
│   ├── 01_data_acquisition.ipynb  # Descarga de fuentes
│   ├── 02_feature_engineering.ipynb  # Generación de variables
│   ├── 03_modeling.ipynb          # Entrenamiento y validación
│   └── 04_mapping.ipynb           # Producto cartográfico final
├── src/                           # Funciones auxiliares reutilizables
├── outputs/
│   ├── maps/                      # Mapas y figuras
│   └── results/                   # Productos geoespaciales finales
└── docs/
    └── nota_tecnica.pdf           # Documento técnico de la nota
```

## 3. Requisitos

- Python ≥ 3.10
- Cuenta activa de [Google Earth Engine](https://earthengine.google.com/)
- Conexión a internet estable
- ~6 GB de espacio en disco para datos intermedios
- Dependencias listadas en `requirements.txt`

## 4. Instalación

```bash
# Clonar el repositorio
git clone https://github.com/hperezc/GeoAI-specialist-prueba-tecnica-cartagena.git
cd prueba-tecnica-cartagena

# Crear ambiente virtual (recomendado)
python -m venv .venv
source .venv/bin/activate   # macOS / Linux
# .venv\Scripts\activate    # Windows

# Instalar dependencias
pip install -r requirements.txt

# Autenticar Google Earth Engine (primera vez)
earthengine authenticate
```

## 5. Reproducir el flujo

Ejecutar los notebooks en orden:

1. `notebooks/01_data_acquisition.ipynb` — Descarga el perímetro urbano, Sentinel-2/1, GHS-BUILT, OSM, DEM, VIIRS y WorldPop. Genera la grilla de análisis de 100 m × 100 m sobre el área urbana.
2. `notebooks/02_feature_engineering.ipynb` — Calcula índices espectrales (NDVI, NDBI, NDWI, BSI), texturas GLCM, variables topográficas (pendiente, TPI), densidad de edificios y vías OSM, e integra todo en una tabla maestra por celda.
3. `notebooks/03_modeling.ipynb` — Entrena un Random Forest sobre las etiquetas oficiales (CCV) generadas en el notebook 01, con validación cruzada espacial, calcula importancia de variables y genera la probabilidad sobre toda la grilla.
4. `notebooks/04_mapping.ipynb` — Clasifica el raster en 4 niveles por percentiles, genera el mapa final estático con leyenda, y exporta los productos en GeoTIFF y GeoPackage.

## 6. Productos finales

Después de correr el flujo completo, en `outputs/` se generan:

- `outputs/results/probabilidad_asentamientos_informales_cartagena.tif` — Raster de probabilidad continua (0–1) por celda de 100 m
- `outputs/results/asentamientos_informales_clasificado.gpkg` — Capa vectorial de celdas (8,902 polígonos de 100 m × 100 m) con probabilidad y clasificación en 4 niveles
- `outputs/results/zonas_clasificadas_disueltas.gpkg` — Capa vectorial de zonas continuas (celdas contiguas de la misma clase disueltas), con estadísticas agregadas por zona (probabilidad media/mín/máx, área, número de celdas)
- `outputs/results/asentamientos_informales_cartagena.geojson` — GeoJSON simplificado para uso web
- `outputs/maps/mapa_final.pdf` y `mapa_clases.pdf` — Mapas cartográficos estáticos para difusión
- `docs/nota_tecnica.pdf` — Documento técnico completo

## 7. Resumen metodológico

| Componente | Decisión técnica |
|---|---|
| **Tipo de enfoque** | Clasificación supervisada binaria a nivel de celda |
| **Modelo** | Random Forest (200 árboles) + calibración Platt |
| **Resolución de análisis** | Grilla de 100 m × 100 m sobre el perímetro urbano |
| **Perímetro urbano** | DANE MGN 2024, capa MGN_URB_ZONA_URBANA, descargada del geoportal Colombia en Mapas (IGAC) |
| **Fuentes satelitales** | Sentinel-2 SR (30 m), Sentinel-1 GRD (20 m), Copernicus DEM (30 m) |
| **Fuentes auxiliares** | GHS-BUILT (JRC), VIIRS (NOAA), WorldPop, OpenStreetMap |
| **Estrategia de etiquetado** | Polígonos oficiales por nombre desde la capa "Barrios de Cartagena" de Cartagena Cómo Vamos (CCV) — 33 barrios informales y 17 formales distribuidos por toda la ciudad |
| **Validación** | Cross-validation espacial con `GroupKFold` sobre bloques geográficos 4×4 |
| **Métricas CV** | F1 0.82 ± 0.12, AUC 0.91 ± 0.06, Precision 0.83, Recall 0.82 |
| **Salida** | Probabilidad continua por celda, clasificada en 4 niveles por percentiles |

Para la justificación detallada de cada decisión, consulte `docs/nota_tecnica.pdf`.

## 8. Limitaciones reconocidas

Este producto es un **insumo preliminar** para orientar análisis urbanos y trabajo de campo, no un diagnóstico final. Sus limitaciones principales — documentadas en detalle en la nota técnica — incluyen:

- Las etiquetas positivas no están validadas en campo
- El modelo puede tener bajo desempeño en tipologías de asentamiento informal subrepresentadas en las etiquetas
- La definición de "informal" no es binaria; existe un gradiente de consolidación
- Las imágenes corresponden a un momento temporal específico

Cualquier uso operativo del producto **requiere validación experta y revisión humana en el loop**.

## 9. Licencia

Este trabajo se entrega como parte de una prueba técnica para ONU-Hábitat. Los datos utilizados provienen de fuentes públicas con sus respectivas licencias (Copernicus, OpenStreetMap, NASA, JRC, WorldPop).

## 10. Contacto

Héctor Camilo Pérez Contreras
hectorcperez21@gmail.com
[LinkedIn](https://www.linkedin.com/in/hector-camilo-perez-contreras-a971551a1/) | [GitHub](https://github.com/hperezc)
