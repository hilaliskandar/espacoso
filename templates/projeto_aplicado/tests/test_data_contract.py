"""Testes de contrato dos dados e da fixture sintética."""

from __future__ import annotations

import geopandas as gpd
import pytest
from shapely.geometry import box


REQUIRED_COLUMNS = {"id", "indicador"}


def test_demo_gdf_columns(demo_gdf):
    """Fixture deve conter as colunas obrigatórias."""
    assert REQUIRED_COLUMNS.issubset(set(demo_gdf.columns))


def test_demo_gdf_crs(demo_gdf):
    """Fixture deve ter CRS definido."""
    assert demo_gdf.crs is not None


def test_demo_gdf_no_null_geometry(demo_gdf):
    """Fixture não deve ter geometrias nulas."""
    assert demo_gdf.geometry.notna().all()


def test_demo_gdf_valid_geometry(demo_gdf):
    """Todas as geometrias da fixture devem ser válidas."""
    assert demo_gdf.geometry.is_valid.all()


def test_demo_gdf_unique_ids(demo_gdf):
    """Identificadores da fixture devem ser únicos."""
    assert demo_gdf["id"].nunique() == len(demo_gdf)


def test_demo_gdf_indicador_not_null(demo_gdf):
    """Indicador não deve ter valores nulos."""
    assert demo_gdf["indicador"].notna().all()


def test_schema_validation(demo_gdf):
    """Fixture deve passar na validação do esquema mínimo esperado."""
    for col in REQUIRED_COLUMNS:
        assert col in demo_gdf.columns, f"Coluna obrigatória ausente: {col}"
    assert demo_gdf.geometry.geom_type.isin(
        ["Polygon", "MultiPolygon"]
    ).all(), "Geometrias devem ser polígonos"
