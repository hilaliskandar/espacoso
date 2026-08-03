import numpy as np

from autocorrelacao_espacial.multiple_testing import benjamini_hochberg
from autocorrelacao_espacial.statistics import geary_c, getis_ord_g_star, local_moran, moran_i, permutation_global
from autocorrelacao_espacial.weights import WeightMatrix


def line_weights() -> WeightMatrix:
    return WeightMatrix(
        name="line",
        ids=("a", "b", "c", "d"),
        neighbors=((1,), (0, 2), (1, 3), (2,)),
        weights=((1.0,), (0.5, 0.5), (0.5, 0.5), (1.0,)),
        transform="row_standardized",
        kind="custom",
        metadata={},
    )


def test_known_global_statistics():
    x = np.array([1.0, 2.0, 3.0, 4.0])
    w = line_weights()
    assert np.isclose(moran_i(x, w), 0.4)
    assert np.isclose(geary_c(x, w), 0.3)


def test_global_permutations_are_reproducible():
    x = np.array([1.0, 2.0, 3.0, 4.0])
    w = line_weights()
    first = permutation_global(x, w, "moran", 99, 42, "two-sided")
    second = permutation_global(x, w, "moran", 99, 42, "two-sided")
    assert first == second
    assert 0 < first.p_value <= 1


def test_local_moran_has_expected_columns():
    x = np.array([1.0, 2.0, 3.0, 4.0])
    result = local_moran(x, line_weights(), 99, 123, 0.05, True)
    assert {"local_moran", "p_value", "q_value", "cluster"}.issubset(result.columns)
    assert set(result["cluster"]).issubset({"HH", "LL", "HL", "LH", "NS", "Island"})


def test_getis_ord_is_finite():
    x = np.array([1.0, 2.0, 3.0, 4.0])
    result = getis_ord_g_star(x, line_weights(), 99, 123, 0.05, True)
    assert np.isfinite(result["g_star"]).all()
    assert set(result["classification"]).issubset({"Hot", "Cold", "NS"})


def test_benjamini_hochberg_monotone_in_rank():
    p = np.array([0.01, 0.04, 0.03, 0.2])
    q = benjamini_hochberg(p)
    order = np.argsort(p)
    assert np.all(np.diff(q[order]) >= -1e-12)
    assert np.all((0 <= q) & (q <= 1))
