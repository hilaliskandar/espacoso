"""Testes de decomposição de impactos espaciais."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from scipy import sparse

from econometria_espacial.config import SpatialModelSpec
from econometria_espacial.impacts import compute_impacts, impacts_table
from econometria_espacial.models import fit_spatial_model
from econometria_espacial.weights import WeightMatrix


def _make_weights(w: np.ndarray, ids: list[str]) -> WeightMatrix:
    mat = sparse.csr_matrix(w)
    row_sums = np.asarray(mat.sum(axis=1)).ravel()
    islands = tuple(ids[i] for i in np.flatnonzero(row_sums == 0))
    return WeightMatrix("rook", tuple(ids), mat, islands, "row_standardized")


def test_ols_impacts_direct_equals_coefficient(sar_synthetic):
    df, w, _, _ = sar_synthetic
    ids = list(df["id"])
    weights = _make_weights(w, ids)
    spec = SpatialModelSpec("OLS", "OLS", "y", ("x1", "x2"), "rook")
    result = fit_spatial_model(df, spec, weights)
    decomps = compute_impacts(result)
    for d in decomps:
        assert d.indirect == pytest.approx(0.0)
        assert d.total == pytest.approx(d.direct + d.indirect, abs=1e-10)


def test_sar_impacts_sum_to_total(sar_synthetic):
    df, w, _, _ = sar_synthetic
    ids = list(df["id"])
    weights = _make_weights(w, ids)
    spec = SpatialModelSpec("SAR", "SAR", "y", ("x1", "x2"), "rook")
    result = fit_spatial_model(df, spec, weights)
    decomps = compute_impacts(result)
    assert len(decomps) == 2  # x1, x2
    for d in decomps:
        assert d.total == pytest.approx(d.direct + d.indirect, abs=1e-8)


def test_sdm_impacts_sum_to_total(sar_synthetic):
    df, w, _, _ = sar_synthetic
    ids = list(df["id"])
    weights = _make_weights(w, ids)
    spec = SpatialModelSpec("SDM", "SDM", "y", ("x1", "x2"), "rook")
    result = fit_spatial_model(df, spec, weights)
    decomps = compute_impacts(result)
    for d in decomps:
        assert d.total == pytest.approx(d.direct + d.indirect, abs=1e-8)


def test_slx_indirect_equals_theta(sar_synthetic):
    """Para SLX, impacto indireto = θ (coeficiente de W.x)."""
    df, w, _, _ = sar_synthetic
    ids = list(df["id"])
    weights = _make_weights(w, ids)
    spec = SpatialModelSpec("SLX", "SLX", "y", ("x1", "x2"), "rook")
    result = fit_spatial_model(df, spec, weights)
    decomps = compute_impacts(result)
    for d in decomps:
        theta = result.params.get(f"W.{d.term}", 0.0)
        assert d.indirect == pytest.approx(theta, abs=1e-10)


def test_impacts_table_shape(sar_synthetic):
    df, w, _, _ = sar_synthetic
    ids = list(df["id"])
    weights = _make_weights(w, ids)
    results = []
    for mt in ["OLS", "SAR", "SEM", "SLX", "SDM"]:
        spec = SpatialModelSpec(mt, mt, "y", ("x1", "x2"), "rook")
        results.append(fit_spatial_model(df, spec, weights))
    table = impacts_table(results)
    # 5 modelos × 2 preditores = 10 linhas
    assert len(table) == 10
    assert set(table.columns) >= {"model", "model_type", "term", "direct", "indirect", "total"}
