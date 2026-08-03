import numpy as np
import pandas as pd
import pytest

from diagnostico_ols.config import ModelSpec, WeightSpec
from diagnostico_ols.diagnostics import influence_table, lm_tests, moran_i, moran_permutation
from diagnostico_ols.modeling import fit_model
from diagnostico_ols.weights import load_weights


def test_moran_known_chain_value(four_grid):
    _, _, path = four_grid
    weights = load_weights(WeightSpec(name="line", path=path), ["A", "B", "C", "D"])
    assert moran_i(np.array([1.0, 2.0, 3.0, 4.0]), weights) == pytest.approx(0.4)


def test_moran_permutation_is_reproducible(four_grid):
    _, _, path = four_grid
    weights = load_weights(WeightSpec(name="line", path=path), ["A", "B", "C", "D"])
    values = np.array([1.0, 2.0, 3.0, 4.0])
    assert moran_permutation(values, weights, 99, 9) == moran_permutation(values, weights, 99, 9)


def test_influence_identifies_outlier():
    x = np.arange(20.0)
    y = 1 + 2 * x
    y[-1] += 30
    model = fit_model(pd.DataFrame({"y": y, "x": x}), ModelSpec("outlier", "y", ("x",)))
    table = influence_table(model, [str(i) for i in range(20)])
    assert table.loc[table["cooks_distance"].idxmax(), "id"] == "19"


def test_lm_statistics_are_nonnegative(four_grid):
    _, _, path = four_grid
    weights = load_weights(WeightSpec(name="line", path=path), ["A", "B", "C", "D"])
    data = pd.DataFrame({"y": [1.0, 2.5, 4.2, 8.0], "x": [0.0, 1.0, 2.0, 3.0]})
    model = fit_model(data, ModelSpec("lm", "y", ("x",)))
    result = lm_tests(model, weights)
    for key in ["lm_error", "lm_lag", "lm_sarma"]:
        assert np.isnan(result[key]) or result[key] >= 0
