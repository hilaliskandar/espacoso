"""Leitura e preparação de dados espaciais para a rede."""
from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import pandas as pd

from .errors import ConfigError


def read_spatial(path: Path, layer: str | None = None) -> gpd.GeoDataFrame:
    """Lê arquivo espacial em GeoDataFrame."""
    if not path.exists():
        raise ConfigError(f"Arquivo não encontrado: {path}")
    kwargs: dict = {"filename": str(path)}
    if layer:
        kwargs["layer"] = layer
    return gpd.read_file(**kwargs)


def prepare_network(
    gdf: gpd.GeoDataFrame,
    analysis_crs: str,
) -> gpd.GeoDataFrame:
    """Reprojecta rede para CRS de análise e garante geometria LineString."""
    if gdf.crs is None:
        raise ConfigError("A rede não possui CRS definido.")
    gdf = gdf.to_crs(analysis_crs)
    if not all(gdf.geometry.geom_type.isin(["LineString", "MultiLineString"])):
        invalid = gdf.geometry.geom_type[
            ~gdf.geometry.geom_type.isin(["LineString", "MultiLineString"])
        ].unique()
        raise ConfigError(f"A rede deve conter apenas linhas; encontrado: {list(invalid)}.")
    gdf = gdf.copy()
    gdf["length_m"] = gdf.geometry.length
    return gdf


def prepare_origins(
    gdf: gpd.GeoDataFrame,
    id_column: str,
    opportunities_column: str,
    population_column: str,
    analysis_crs: str,
) -> gpd.GeoDataFrame:
    """Valida e reprojecta unidades de origem."""
    if gdf.crs is None:
        raise ConfigError("As origens não possuem CRS definido.")
    gdf = gdf.to_crs(analysis_crs)
    for col in (id_column, opportunities_column, population_column):
        if col not in gdf.columns:
            raise ConfigError(f"Coluna obrigatória ausente nas origens: {col!r}.")
    gdf = gdf.copy()
    gdf[opportunities_column] = pd.to_numeric(gdf[opportunities_column], errors="coerce")
    gdf[population_column] = pd.to_numeric(gdf[population_column], errors="coerce")
    return gdf
