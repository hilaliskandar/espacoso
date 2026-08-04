from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

from .config import AnalysisConfig


def read_geodata(config: AnalysisConfig) -> gpd.GeoDataFrame:
    path = config.input_path
    if path.suffix.lower() in {".gpkg", ".shp", ".geojson", ".json"}:
        gdf = gpd.read_file(path, layer=config.geometry_layer)
    else:
        raise ValueError(f"Formato de arquivo não suportado: {path.suffix}")
    if gdf.empty:
        raise ValueError(f"Nenhum dado encontrado em: {path}")
    if config.id_column not in gdf.columns:
        raise ValueError(f"Coluna de ID ausente: {config.id_column}")
    missing = [c for c in (config.target, *config.predictors) if c not in gdf.columns]
    if missing:
        raise ValueError(f"Colunas ausentes nos dados: {missing}")
    return gdf


def extract_coordinates(gdf: gpd.GeoDataFrame) -> np.ndarray:
    """Return (n, 2) array of projected centroid coordinates."""
    centroids = gdf.geometry.centroid
    return np.column_stack([centroids.x.to_numpy(), centroids.y.to_numpy()])


def build_design(
    gdf: gpd.GeoDataFrame,
    target: str,
    predictors: tuple[str, ...],
    add_constant: bool,
) -> tuple[np.ndarray, np.ndarray, list[str]]:
    import statsmodels.api as sm

    y = gdf[target].astype(float).to_numpy()
    x_df = gdf[list(predictors)].astype(float)
    if add_constant:
        x_df = sm.add_constant(x_df, has_constant="add")
    feature_names = list(x_df.columns)
    return y, x_df.to_numpy(), feature_names


def write_geodata(gdf: gpd.GeoDataFrame, path: Path, layer: str = "result") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    gdf.to_file(path, layer=layer, driver="GPKG")
