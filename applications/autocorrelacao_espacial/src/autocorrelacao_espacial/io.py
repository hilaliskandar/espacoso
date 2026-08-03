from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import pandas as pd

from .errors import DataError


def read_spatial(path: Path, layer: str | None = None) -> gpd.GeoDataFrame:
    if not path.exists():
        raise DataError(f"Arquivo espacial não encontrado: {path}")
    try:
        gdf = gpd.read_file(path, layer=layer)
    except Exception as exc:
        raise DataError(f"Falha ao ler arquivo espacial {path}: {exc}") from exc
    if gdf.empty:
        raise DataError("O arquivo espacial não contém observações.")
    if gdf.geometry.name not in gdf.columns:
        raise DataError("Coluna de geometria ausente.")
    return gdf


def validate_and_prepare(
    gdf: gpd.GeoDataFrame,
    id_column: str,
    value_column: str,
    analysis_crs: str,
) -> gpd.GeoDataFrame:
    missing = [c for c in (id_column, value_column) if c not in gdf.columns]
    if missing:
        raise DataError(f"Colunas obrigatórias ausentes: {missing}")
    if gdf.crs is None:
        raise DataError("O arquivo espacial não possui CRS declarado.")
    if gdf[id_column].isna().any():
        raise DataError("A coluna de identificação contém valores ausentes.")
    normalized = gdf[id_column].astype(str).str.strip()
    if normalized.eq("").any():
        raise DataError("A coluna de identificação contém chaves vazias.")
    if normalized.duplicated().any():
        duplicates = sorted(normalized[normalized.duplicated(keep=False)].unique().tolist())
        raise DataError(f"Chaves duplicadas após normalização: {duplicates[:10]}")
    values = pd.to_numeric(gdf[value_column], errors="coerce")
    if values.isna().any():
        raise DataError("A variável de análise contém valores ausentes ou não numéricos.")
    if values.nunique(dropna=True) < 2:
        raise DataError("A variável de análise precisa apresentar variação.")
    if gdf.geometry.isna().any() or gdf.geometry.is_empty.any():
        raise DataError("Há geometrias ausentes ou vazias.")
    invalid = ~gdf.geometry.is_valid
    if invalid.any():
        raise DataError(f"Há {int(invalid.sum())} geometrias inválidas. Execute a A1 antes da A2.")
    prepared = gdf.copy()
    prepared[id_column] = normalized
    prepared[value_column] = values.astype(float)
    try:
        prepared = prepared.to_crs(analysis_crs)
    except Exception as exc:
        raise DataError(f"Falha ao reprojetar para {analysis_crs}: {exc}") from exc
    if prepared.crs is None or prepared.crs.is_geographic:
        raise DataError("analysis_crs deve ser projetado para matrizes baseadas em distância.")
    prepared = prepared.sort_values(id_column, kind="stable").reset_index(drop=True)
    return prepared
