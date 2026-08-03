from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

from .config import AnalysisConfig
from .errors import DataError


def read_geodata(config: AnalysisConfig) -> gpd.GeoDataFrame:
    if not config.input_path.exists():
        raise DataError(f"Arquivo espacial não encontrado: {config.input_path}")
    kwargs = {"layer": config.geometry_layer} if config.geometry_layer else {}
    gdf = gpd.read_file(config.input_path, **kwargs)
    if config.id_column not in gdf.columns:
        raise DataError(f"Coluna identificadora ausente: {config.id_column}")
    if gdf.crs is None:
        raise DataError("O arquivo espacial não possui CRS.")
    if gdf.geometry.isna().any() or gdf.geometry.is_empty.any():
        raise DataError("Há geometrias ausentes ou vazias.")
    if not gdf.geometry.is_valid.all():
        raise DataError("Há geometrias inválidas; trate-as na A1.")

    gdf = gdf.copy()
    gdf[config.id_column] = gdf[config.id_column].astype(str).str.strip()
    if gdf[config.id_column].duplicated().any():
        duplicated = gdf.loc[gdf[config.id_column].duplicated(), config.id_column].tolist()
        raise DataError(f"Identificadores duplicados: {duplicated[:5]}")

    required: set[str] = set()
    for model in config.models:
        required.add(model.target)
        required.update(model.predictors)
    missing = sorted(required.difference(gdf.columns))
    if missing:
        raise DataError(f"Colunas de modelagem ausentes: {missing}")
    for column in sorted(required):
        numeric = pd.to_numeric(gdf[column], errors="coerce")
        if numeric.isna().any() or not np.isfinite(numeric.to_numpy()).all():
            raise DataError(f"A coluna {column} contém valores ausentes ou não numéricos.")
        gdf[column] = numeric.astype(float)
    return gdf


def write_geodata(gdf: gpd.GeoDataFrame, path: Path, layer: str = "diagnostico") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path.unlink()
    gdf.to_file(path, layer=layer, driver="GPKG")
