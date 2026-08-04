from __future__ import annotations

import geopandas as gpd
import numpy as np
import pytest

from maup_sensibilidade.aggregation import aggregate
from maup_sensibilidade.config import SchemeSpec
from maup_sensibilidade.errors import DataError
from maup_sensibilidade.statistics import (
    MoranResult,
    contiguity_matrix,
    descriptive_stats,
    moran_i,
    permutation_moran,
    stability_table,
)


def test_contiguity_matrix_row_standardized(grid_gdf: gpd.GeoDataFrame) -> None:
    scheme = SchemeSpec(name="meso", dissolve_column="meso_id", weight_column=None)
    agg = aggregate(grid_gdf, scheme, ("renda",))
    w = contiguity_matrix(agg)
    assert w.shape == (len(agg), len(agg))
    # row sums must be 0 (island) or 1
    row_sums = w.sum(axis=1)
    assert np.all((np.isclose(row_sums, 0) | np.isclose(row_sums, 1)))


def test_moran_i_range(grid_gdf: gpd.GeoDataFrame) -> None:
    scheme = SchemeSpec(name="meso", dissolve_column="meso_id", weight_column=None)
    agg = aggregate(grid_gdf, scheme, ("renda",))
    w = contiguity_matrix(agg)
    vals = agg["renda_mean"].to_numpy(dtype=float)
    mi = moran_i(vals, w)
    assert -2 < mi < 2


def test_permutation_moran_reproducible(grid_gdf: gpd.GeoDataFrame) -> None:
    scheme = SchemeSpec(name="meso", dissolve_column="meso_id", weight_column=None)
    agg = aggregate(grid_gdf, scheme, ("renda",))
    w = contiguity_matrix(agg)
    vals = agg["renda_mean"].to_numpy(dtype=float)
    r1 = permutation_moran(vals, w, 99, 42)
    r2 = permutation_moran(vals, w, 99, 42)
    assert r1.moran_i == r2.moran_i
    assert r1.p_value == r2.p_value
    assert 0 < r1.p_value <= 1


def test_moran_zero_variance_raises(grid_gdf: gpd.GeoDataFrame) -> None:
    scheme = SchemeSpec(name="meso", dissolve_column="meso_id", weight_column=None)
    agg = aggregate(grid_gdf, scheme, ("renda",))
    w = contiguity_matrix(agg)
    constant = np.ones(len(agg))
    with pytest.raises(DataError):
        permutation_moran(constant, w, 99, 42)


def test_descriptive_stats(grid_gdf: gpd.GeoDataFrame) -> None:
    scheme = SchemeSpec(name="meso", dissolve_column="meso_id", weight_column=None)
    agg = aggregate(grid_gdf, scheme, ("renda",))
    desc = descriptive_stats({"meso": agg}, ("renda",))
    assert "mean" in desc.columns
    assert "std" in desc.columns
    assert "n" in desc.columns
    assert len(desc) == 1


def test_stability_table(grid_gdf: gpd.GeoDataFrame) -> None:
    scheme_micro = SchemeSpec(name="micro", dissolve_column=None, weight_column=None)
    scheme_meso = SchemeSpec(name="meso", dissolve_column="meso_id", weight_column=None)
    agg_micro = aggregate(grid_gdf, scheme_micro, ("renda",))
    agg_meso = aggregate(grid_gdf, scheme_meso, ("renda",))
    w_micro = contiguity_matrix(agg_micro)
    w_meso = contiguity_matrix(agg_meso)
    r_micro = permutation_moran(agg_micro["renda_mean"].to_numpy(), w_micro, 99, 1)
    r_meso = permutation_moran(agg_meso["renda_mean"].to_numpy(), w_meso, 99, 2)
    stab = stability_table({"renda": {"micro": r_micro, "meso": r_meso}})
    assert "sign_stable" in stab.columns
    assert "significance_stable" in stab.columns
    assert "std_i_across_schemes" in stab.columns
