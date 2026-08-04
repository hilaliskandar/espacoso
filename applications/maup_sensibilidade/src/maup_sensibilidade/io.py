from __future__ import annotations

from pathlib import Path

import geopandas as gpd

from .config import AnalysisConfig
from .errors import DataError


def read_geodata(config: AnalysisConfig) -> gpd.GeoDataFrame:
    path = config.input_path
    if not path.exists():
        raise DataError(f"Arquivo de entrada não encontrado: {path}")
    kwargs: dict = {}
    if config.geometry_layer:
        kwargs["layer"] = config.geometry_layer
    gdf: gpd.GeoDataFrame = gpd.read_file(path, **kwargs)
    if config.id_column not in gdf.columns:
        raise DataError(f"Coluna de identificação ausente: {config.id_column}")
    for var in config.variables:
        if var not in gdf.columns:
            raise DataError(f"Variável ausente na camada: {var}")
    if gdf[config.id_column].duplicated().any():
        raise DataError(f"Coluna {config.id_column!r} contém identificadores duplicados.")
    return gdf


def write_geodata(gdf: gpd.GeoDataFrame, path: Path, layer: str = "dados") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path.unlink()
    gdf.to_file(path, layer=layer, driver="GPKG")
