import numpy as np

from src.metrics import (
    conformal_quantile,
    interval_metrics,
    local_moran,
    moran_i,
    regression_metrics,
)


def test_regression_metrics_perfect_prediction():
    y = np.array([1.0, 2.0, 3.0])
    m = regression_metrics(y, y)
    assert m["rmse"] == 0
    assert m["mae"] == 0
    assert m["r2"] == 1


def test_interval_metrics():
    y = np.array([1.0, 2.0, 3.0])
    lower = np.array([0.0, 1.0, 3.1])
    upper = np.array([2.0, 3.0, 4.0])
    m = interval_metrics(y, lower, upper)
    assert np.isclose(m["interval_coverage"], 2 / 3)
    assert m["interval_width"] > 0


def test_conformal_quantile_is_observed_residual():
    residuals = np.array([0.1, 0.2, 0.3, 0.4])
    q = conformal_quantile(residuals, 0.75)
    assert q in residuals


def test_moran_returns_finite_values_for_two_weights():
    coords = np.array([[0, 0], [1, 0], [0, 1], [1, 1], [2, 1]], dtype=float)
    values = np.array([1.0, 1.2, 2.0, 2.2, 3.0])
    for weighting in ["uniform", "inverse_distance"]:
        i, p = moran_i(values, coords, k=2, weighting=weighting, permutations=19, seed=1)
        assert np.isfinite(i)
        assert 0 <= p <= 1


def test_local_moran_shapes_and_labels():
    rng = np.random.default_rng(4)
    coords = rng.uniform(size=(30, 2))
    values = np.sin(coords[:, 0] * 5) + np.cos(coords[:, 1] * 4)
    result = local_moran(values, coords, k=4, permutations=19, seed=2)
    assert len(result["local_i"]) == 30
    assert set(np.unique(result["cluster"])).issubset({"NS", "HH", "LL", "HL", "LH"})
