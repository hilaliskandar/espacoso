from __future__ import annotations

import numpy as np
import statsmodels.api as sm
import pytest

from heterogeneidade_espacial.gwr_model import (
    fit_gwr,
    gwr_coefficient_table,
    gwr_summary,
    local_collinearity,
)
from heterogeneidade_espacial.config import BandwidthSpec
from heterogeneidade_espacial.diagnostics import coefficient_variability, comparison_table
from heterogeneidade_espacial.global_model import fit_global


@pytest.fixture
def small_grid():
    rng = np.random.default_rng(7)
    n = 25
    side = 5
    cx = np.tile(np.arange(side, dtype=float) + 0.5, side)
    cy = np.repeat(np.arange(side, dtype=float) + 0.5, side)
    coords = np.column_stack([cx, cy])
    x1 = rng.normal(0, 1, n)
    x2 = rng.normal(0, 1, n)
    beta1 = 1.0 + cx / cx.max()
    y = 2.0 + beta1 * x1 + 0.5 * x2 + rng.normal(0, 0.3, n)
    x = sm.add_constant(np.column_stack([x1, x2]))
    feature_names = ["const", "x1", "x2"]
    ids = [f"c{i}" for i in range(n)]
    return coords, y, x, feature_names, ids


def test_fit_gwr_shapes(small_grid):
    coords, y, x, feature_names, ids = small_grid
    spec = BandwidthSpec(criterion="AICc", kernel="bisquare",
                         fixed_or_adaptive="adaptive", search_method="golden_section")
    res = fit_gwr(coords, y, x, feature_names, spec)
    n, k = len(y), len(feature_names)
    assert res.params.shape == (n, k)
    assert res.fitted.shape == (n,)
    assert res.residuals.shape == (n,)
    assert res.feature_names == feature_names


def test_gwr_coefficient_table(small_grid):
    coords, y, x, feature_names, ids = small_grid
    spec = BandwidthSpec(criterion="AICc", kernel="bisquare",
                         fixed_or_adaptive="adaptive", search_method="golden_section")
    res = fit_gwr(coords, y, x, feature_names, spec)
    df = gwr_coefficient_table(res, ids)
    assert set(df.columns) >= {"model", "id", "term", "coefficient", "std_error", "ci_low", "ci_high"}
    assert len(df) == len(y) * len(feature_names)


def test_coefficient_variability(small_grid):
    coords, y, x, feature_names, ids = small_grid
    spec = BandwidthSpec(criterion="AICc", kernel="bisquare",
                         fixed_or_adaptive="adaptive", search_method="golden_section")
    res = fit_gwr(coords, y, x, feature_names, spec)
    var = coefficient_variability(res)
    assert len(var) == len(feature_names)
    assert "iqr" in var.columns


def test_comparison_table(small_grid):
    coords, y, x, feature_names, ids = small_grid
    spec = BandwidthSpec(criterion="AICc", kernel="bisquare",
                         fixed_or_adaptive="adaptive", search_method="golden_section")
    gwr_res = fit_gwr(coords, y, x, feature_names, spec)
    global_res = fit_global(y, x, feature_names)
    comp = comparison_table(global_res, gwr_res)
    assert "OLS_global" in comp["model"].values
    assert "GWR" in comp["model"].values
    assert "aic" in comp.columns


def test_local_collinearity(small_grid):
    coords, y, x, feature_names, ids = small_grid
    spec = BandwidthSpec(criterion="AICc", kernel="bisquare",
                         fixed_or_adaptive="adaptive", search_method="golden_section")
    res = fit_gwr(coords, y, x, feature_names, spec)
    coll = local_collinearity(res)
    assert len(coll) == len(y)
    assert "local_coef_se_max" in coll.columns
