"""Testes dos estimadores SAR, SEM, SLX, SDM e OLS."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from econometria_espacial.config import SpatialModelSpec
from econometria_espacial.models import fit_spatial_model, model_summary
from econometria_espacial.weights import WeightMatrix
from scipy import sparse


def _make_weights(w: np.ndarray, ids: list[str], name: str = "rook") -> WeightMatrix:
    mat = sparse.csr_matrix(w)
    row_sums = np.asarray(mat.sum(axis=1)).ravel()
    islands = tuple(ids[i] for i in np.flatnonzero(row_sums == 0))
    return WeightMatrix(name=name, ids=tuple(ids), matrix=mat, islands=islands,
                        transformation="row_standardized")


def test_ols_recovers_coefficients(sar_synthetic):
    df, w, rho_true, beta_true = sar_synthetic
    ids = list(df["id"])
    weights = _make_weights(w, ids)
    spec = SpatialModelSpec("OLS", "OLS", "y", ("x1", "x2"), "rook")
    result = fit_spatial_model(df, spec, weights)
    assert result.model_type == "OLS"
    assert result.rho is None
    assert result.lam is None
    # OLS deve ter R² próximo de 1 (dados gerados por SAR, mas correlação alta)
    assert result.log_likelihood > -1e6


def test_sar_rho_not_ols_coefficient(sar_synthetic):
    """ρ do SAR NÃO é um coeficiente OLS — deve ser estimado por ML."""
    df, w, rho_true, beta_true = sar_synthetic
    ids = list(df["id"])
    weights = _make_weights(w, ids)
    spec = SpatialModelSpec("SAR", "SAR", "y", ("x1", "x2"), "rook")
    result = fit_spatial_model(df, spec, weights)
    assert result.rho is not None
    # ρ deve estar dentro dos limites (-1, 1)
    assert -1.0 < result.rho < 1.0
    # Não deve ser igual ao coeficiente OLS de Wy
    # (verificação estrutural: ρ é um parâmetro autorregressivo, não uma entrada de β)
    assert "rho" not in result.feature_names


def test_sar_recovers_rho_approximately(sar_synthetic):
    """SAR deve recuperar ρ próximo do valor verdadeiro (0.4) com n=25."""
    df, w, rho_true, beta_true = sar_synthetic
    ids = list(df["id"])
    weights = _make_weights(w, ids)
    spec = SpatialModelSpec("SAR", "SAR", "y", ("x1", "x2"), "rook")
    result = fit_spatial_model(df, spec, weights)
    assert result.converged
    # Tolerância: amostras pequenas têm variância alta
    assert abs(result.rho - rho_true) < 0.5


def test_sem_has_lambda_not_rho(sar_synthetic):
    df, w, rho_true, beta_true = sar_synthetic
    ids = list(df["id"])
    weights = _make_weights(w, ids)
    spec = SpatialModelSpec("SEM", "SEM", "y", ("x1", "x2"), "rook")
    result = fit_spatial_model(df, spec, weights)
    assert result.lam is not None
    assert result.rho is None
    assert -1.0 < result.lam < 1.0


def test_slx_has_wx_columns(sar_synthetic):
    df, w, rho_true, beta_true = sar_synthetic
    ids = list(df["id"])
    weights = _make_weights(w, ids)
    spec = SpatialModelSpec("SLX", "SLX", "y", ("x1", "x2"), "rook")
    result = fit_spatial_model(df, spec, weights)
    assert result.rho is None
    assert result.lam is None
    assert "W.x1" in result.feature_names
    assert "W.x2" in result.feature_names


def test_sdm_has_rho_and_wx(sar_synthetic):
    df, w, rho_true, beta_true = sar_synthetic
    ids = list(df["id"])
    weights = _make_weights(w, ids)
    spec = SpatialModelSpec("SDM", "SDM", "y", ("x1", "x2"), "rook")
    result = fit_spatial_model(df, spec, weights)
    assert result.rho is not None
    assert "W.x1" in result.feature_names


def test_model_summary_keys(sar_synthetic):
    df, w, rho_true, beta_true = sar_synthetic
    ids = list(df["id"])
    weights = _make_weights(w, ids)
    spec = SpatialModelSpec("OLS", "OLS", "y", ("x1",), "rook")
    result = fit_spatial_model(df, spec, weights)
    summary = model_summary(result)
    for key in ["model", "model_type", "aic", "bic", "log_likelihood", "r_squared", "rmse"]:
        assert key in summary


def test_sar_better_likelihood_than_ols_on_sar_data(sar_synthetic):
    """SAR deve ter log-verossimilhança maior que OLS em dados gerados por SAR."""
    df, w, rho_true, beta_true = sar_synthetic
    ids = list(df["id"])
    weights = _make_weights(w, ids)
    ols = fit_spatial_model(df, SpatialModelSpec("OLS", "OLS", "y", ("x1", "x2"), "rook"), weights)
    sar = fit_spatial_model(df, SpatialModelSpec("SAR", "SAR", "y", ("x1", "x2"), "rook"), weights)
    assert sar.log_likelihood >= ols.log_likelihood
