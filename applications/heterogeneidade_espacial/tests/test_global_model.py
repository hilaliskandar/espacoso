from __future__ import annotations

import numpy as np
import statsmodels.api as sm

from heterogeneidade_espacial.global_model import (
    fit_global,
    global_coefficient_table,
    global_summary,
    vif_table,
)


def test_fit_global_basic():
    rng = np.random.default_rng(0)
    n = 50
    x1 = rng.normal(0, 1, n)
    x2 = rng.normal(0, 1, n)
    y = 2 + 3 * x1 - x2 + rng.normal(0, 0.3, n)
    x = sm.add_constant(np.column_stack([x1, x2]))
    feature_names = ["const", "x1", "x2"]
    res = fit_global(y, x, feature_names)
    assert res.r_squared > 0.8
    assert len(res.params) == 3
    assert res.residuals.shape == (n,)


def test_global_coefficient_table():
    rng = np.random.default_rng(1)
    n = 30
    x = sm.add_constant(rng.normal(0, 1, (n, 2)))
    y = x @ np.array([1.0, 2.0, -1.0]) + rng.normal(0, 0.2, n)
    res = fit_global(y, x, ["const", "a", "b"])
    df = global_coefficient_table(res)
    assert list(df.columns) == ["model", "term", "coefficient", "std_error", "t_value",
                                 "p_value", "ci_low", "ci_high"]
    assert len(df) == 3


def test_vif_table_no_const():
    rng = np.random.default_rng(2)
    n = 40
    x = sm.add_constant(rng.normal(0, 1, (n, 2)))
    res = fit_global(rng.normal(0, 1, n), x, ["const", "x1", "x2"])
    df = vif_table(x, ["const", "x1", "x2"])
    assert "const" not in df["term"].values
    assert len(df) == 2


def test_global_summary_keys():
    rng = np.random.default_rng(3)
    n = 20
    x = sm.add_constant(rng.normal(0, 1, (n, 1)))
    y = rng.normal(0, 1, n)
    res = fit_global(y, x, ["const", "x1"])
    s = global_summary(res)
    for key in ("model", "n", "r_squared", "aic", "bic", "rmse"):
        assert key in s
