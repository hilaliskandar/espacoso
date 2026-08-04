from __future__ import annotations

import geopandas as gpd
import numpy as np
import pytest

from maup_sensibilidade.aggregation import aggregate, verify_total_conservation
from maup_sensibilidade.config import SchemeSpec
from maup_sensibilidade.errors import AggregationError


def test_aggregate_without_dissolve(grid_gdf: gpd.GeoDataFrame) -> None:
    scheme = SchemeSpec(name="micro", dissolve_column=None, weight_column=None)
    agg = aggregate(grid_gdf, scheme, ("renda",))
    assert len(agg) == len(grid_gdf)
    assert "renda_mean" in agg.columns
    assert "renda_sum" in agg.columns
    assert "n_units" in agg.columns
    assert (agg["n_units"] == 1).all()


def test_aggregate_with_dissolve(grid_gdf: gpd.GeoDataFrame) -> None:
    scheme = SchemeSpec(name="meso", dissolve_column="meso_id", weight_column=None)
    agg = aggregate(grid_gdf, scheme, ("renda",))
    # 4×4 grid dissolvido em blocos 2×2 → 4 grupos
    assert len(agg) == 4
    assert "renda_mean" in agg.columns


def test_aggregate_with_weights(grid_gdf: gpd.GeoDataFrame) -> None:
    scheme = SchemeSpec(name="meso", dissolve_column="meso_id", weight_column="populacao")
    agg = aggregate(grid_gdf, scheme, ("renda",))
    assert len(agg) == 4
    assert np.isfinite(agg["renda_mean"]).all()


def test_total_conservation(grid_gdf: gpd.GeoDataFrame) -> None:
    scheme = SchemeSpec(name="meso", dissolve_column="meso_id", weight_column=None)
    agg = aggregate(grid_gdf, scheme, ("renda", "populacao"))
    result = verify_total_conservation(grid_gdf, agg, ("renda", "populacao"))
    assert result["renda"] is True
    assert result["populacao"] is True


def test_missing_dissolve_column_raises(grid_gdf: gpd.GeoDataFrame) -> None:
    scheme = SchemeSpec(name="bad", dissolve_column="nonexistent", weight_column=None)
    with pytest.raises(AggregationError):
        aggregate(grid_gdf, scheme, ("renda",))


def test_missing_weight_column_raises(grid_gdf: gpd.GeoDataFrame) -> None:
    scheme = SchemeSpec(name="bad", dissolve_column="meso_id", weight_column="nonexistent")
    with pytest.raises(AggregationError):
        aggregate(grid_gdf, scheme, ("renda",))


def test_aggregated_geometry_is_valid(grid_gdf: gpd.GeoDataFrame) -> None:
    scheme = SchemeSpec(name="meso", dissolve_column="meso_id", weight_column=None)
    agg = aggregate(grid_gdf, scheme, ("renda",))
    assert agg.geometry.is_valid.all()
