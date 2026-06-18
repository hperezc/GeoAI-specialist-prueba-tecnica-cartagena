"""
Funciones para entrenamiento, validación y predicción del modelo Random Forest.
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import GroupKFold
from sklearn.metrics import (
    classification_report, confusion_matrix,
    roc_auc_score, f1_score, precision_recall_curve,
)
from sklearn.calibration import CalibratedClassifierCV


def construir_split_geografico(df, n_bloques=5, semilla=42):
    """
    Asigna a cada fila un 'grupo geográfico' basado en su posición espacial.
    Se usan tiles aproximadamente iguales en X (longitud) y Y (latitud).
    Devuelve un array de grupos del 0 al n_bloques^2 - 1.

    df debe tener columnas 'centroid_x' y 'centroid_y' (en metros).
    """
    rng = np.random.default_rng(semilla)

    # Cuantiles para dividir en n_bloques en cada eje
    qx = np.linspace(0, 1, n_bloques + 1)
    qy = np.linspace(0, 1, n_bloques + 1)

    # .values puede devolver un array de solo lectura en pandas recientes; se copia.
    cortes_x = df["centroid_x"].quantile(qx).values.copy()
    cortes_y = df["centroid_y"].quantile(qy).values.copy()
    # Asegurar bordes inclusivos
    cortes_x[0] -= 1
    cortes_x[-1] += 1
    cortes_y[0] -= 1
    cortes_y[-1] += 1

    bin_x = np.digitize(df["centroid_x"], cortes_x) - 1
    bin_y = np.digitize(df["centroid_y"], cortes_y) - 1
    bin_x = np.clip(bin_x, 0, n_bloques - 1)
    bin_y = np.clip(bin_y, 0, n_bloques - 1)

    grupo = bin_y * n_bloques + bin_x
    return np.asarray(grupo)


def validacion_cruzada_espacial(X, y, grupos, modelo, verbose=True):
    """
    Cross-validation usando GroupKFold para garantizar separación geográfica
    entre folds. Devuelve diccionario con métricas por fold.
    """
    gkf = GroupKFold(n_splits=min(5, len(np.unique(grupos))))
    resultados = {"f1": [], "auc": [], "precision": [], "recall": []}

    for i, (tr, te) in enumerate(gkf.split(X, y, grupos)):
        modelo_clon = type(modelo)(**modelo.get_params())
        modelo_clon.fit(X[tr], y[tr])
        y_pred = modelo_clon.predict(X[te])
        y_proba = modelo_clon.predict_proba(X[te])[:, 1]

        tp = ((y_pred == 1) & (y[te] == 1)).sum()
        fp = ((y_pred == 1) & (y[te] == 0)).sum()
        fn = ((y_pred == 0) & (y[te] == 1)).sum()
        prec = tp / (tp + fp + 1e-10)
        rec = tp / (tp + fn + 1e-10)
        f1 = 2 * prec * rec / (prec + rec + 1e-10)

        resultados["f1"].append(f1)
        resultados["precision"].append(prec)
        resultados["recall"].append(rec)
        try:
            resultados["auc"].append(roc_auc_score(y[te], y_proba))
        except ValueError:
            resultados["auc"].append(np.nan)

        if verbose:
            print(f"  Fold {i+1}: F1={f1:.3f}  Prec={prec:.3f}  Recall={rec:.3f}")

    return resultados


def threshold_optimo_f1(y_true, y_proba):
    """
    Encuentra el umbral de probabilidad que maximiza F1 sobre la curva PR.
    """
    p, r, t = precision_recall_curve(y_true, y_proba)
    f1 = 2 * p * r / (p + r + 1e-10)
    idx = np.argmax(f1[:-1])  # último valor de t es 1.0 sin umbral asociado
    return t[idx], f1[idx]
