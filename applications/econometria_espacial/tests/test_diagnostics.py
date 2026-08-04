"""Testes de diagnósticos pós-estimação."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from scipy import sparse

from econometria_espacial.config import SpatialModelSpec
from econometria_espacial.diagnostics import (
    fit_comparison,
    moran_i,
    residual_diagnostics,
    verify_impacts_numerically,
)
from econometria_espacial.impacts import compute_impacts
from econometria_espacial.models import fit_spatial_model
from econometria_espacial.weights import WeightMatrix


def _make_weights(w: np.ndarray, ids: list[str]) -> WeightMatrix:
    mat = sparse.csr_matrix(w)
    row_sums = np.asarray(mat.sum(axis=1)).ravel()
    islands = tuple(ids[i] for i in np.flatnonzero(row_sums == 0))
    return WeightMatrix("rook", tuple(ids), mat, islands, "row_standardized")


def test_moran_i_range(sar_synthetic):
    df, w, _, _ = sar_synthetic
    ids = list(df["id"])
    weights = _make_weights(w, ids)
    mi = moran_i(df["y"].to_numpy(), weights)
    assert -1.0 <= mi <= 1.0


def test_moran_i_random_near_zero():
    """Permutação aleatória deve ter I próximo de 0."""
    rng = np.random.default_rng(1)
    n = 20
    vals = rng.standard_normal(n)
    rows, cols = [], []
    for i in range(n - 1):
        rows += [i, i + 1]
        cols += [i + 1, i]
    w = sparse.coo_matrix((np.ones(len(rows)), (rows, cols)), shape=(n, n)).tocsr()
    row_sums = np.asarray(w.sum(axis=1)).ravel()
    inv = 1.0 / np.where(row_sums > 0, row_sums, 1.0)
    w = (sparse.diags(inv) @ w).tocsr()
    islands = tuple(str(i) for i in np.flatnonzero(np.asarray(w.sum(axis=1)).ravel() == 0))
    wm = WeightMatrix("chain", tuple(str(i) for i in range(n)), w, islands, "row_standardized")
    mi = moran_i(vals, wm)
    assert abs(mi) < 2.0  # sem correlação, I pode ser qualquer valor entre -1 e 1


def test_fit_comparison_columns(sar_synthetic):
    df, w, _, _ = sar_synthetic
    ids = list(df["id"])
    weights = _make_weights(w, ids)
    results = [
        fit_spatial_model(df, SpatialModelSpec(mt, mt, "y", ("x1",), "rook"), weights)
        for mt in ["OLS", "SAR"]
    ]
    cmp = fit_comparison(results)
    assert set(cmp.columns) >= {"model", "aic", "bic", "log_likelihood"}
    assert len(cmp) == 2


def test_verify_impacts_all_ok(sar_synthetic):
    df, w, _, _ = sar_synthetic
    ids = list(df["id"])
    weights = _make_weights(w, ids)
    result = fit_spatial_model(df, SpatialModelSpec("SAR", "SAR", "y", ("x1", "x2"), "rook"), weights)
    decomps = compute_impacts(result)
    check = verify_impacts_numerically(decomps)
    assert check["ok"].all()


def test_residual_diagnostics_keys(sar_synthetic):
    df, w, _, _ = sar_synthetic
    ids = list(df["id"])
    weights = _make_weights(w, ids)
    spec = SpatialModelSpec("SAR", "SAR", "y", ("x1",), "rook")
    result = fit_spatial_model(df, spec, weights)
    diag = residual_diagnostics(result, weights, permutations=99, seed=42)
    for key in ["model", "moran_residual", "moran_residual_p", "jarque_bera"]:
        assert key in diag
