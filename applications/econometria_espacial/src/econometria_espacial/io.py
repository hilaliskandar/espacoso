"""I/O para dados geoespaciais."""
from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import pandas as pd

from .config import AnalysisConfig
from .errors import ConfigError


def read_geodata(config: AnalysisConfig) -> gpd.GeoDataFrame:
    if not config.input_path.exists():
        raise ConfigError(f"Arquivo de dados não encontrado: {config.input_path}")
    suffix = config.input_path.suffix.lower()
    if suffix in {".gpkg", ".shp", ".geojson", ".json"}:
        layer = config.geometry_layer
        gdf = gpd.read_file(config.input_path, layer=layer) if layer else gpd.read_file(config.input_path)
    elif suffix == ".csv":
        df = pd.read_csv(config.input_path)
        gdf = gpd.GeoDataFrame(df, geometry=gpd.GeoSeries([None] * len(df)))
    else:
        raise ConfigError(f"Formato de arquivo não suportado: {suffix}")
    if config.id_column not in gdf.columns:
        raise ConfigError(f"Coluna de identificador '{config.id_column}' ausente nos dados.")
    return gdf


def write_geodata(gdf: gpd.GeoDataFrame, path: Path, layer: str = "resultado") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    gdf.to_file(path, layer=layer, driver="GPKG")
