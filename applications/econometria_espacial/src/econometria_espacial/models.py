"""Estimação de modelos econométricos espaciais via máxima verossimilhança.

Modelos suportados
------------------
OLS  — Ordinary Least Squares (referência).
SAR  — Spatial Autoregressive Model (lag na variável dependente).
SEM  — Spatial Error Model (dependência nos erros).
SLX  — Spatial Lag of X (lags das covariadas, estimado por OLS).
SDM  — Spatial Durbin Model (lag em Y e nas covariadas).

Todos os parâmetros autorregressivos (ρ, λ) são estimados por ML, *não* como
coeficientes OLS. Os parâmetros β são estimados por regressão transformada
condicional em ρ ou λ.

Referências
-----------
Anselin, L. (1988). *Spatial Econometrics*. Kluwer.
LeSage, J., Pace, R.K. (2009). *Introduction to Spatial Econometrics*. CRC Press.
"""
from __future__ import annotations

import warnings
from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import optimize, sparse
from scipy.sparse.linalg import spsolve

from .config import SpatialModelSpec
from .errors import EstimationError
from .weights import WeightMatrix


@dataclass
class SpatialModelResult:
    spec: SpatialModelSpec
    model_type: str       # OLS | SAR | SEM | SLX | SDM
    params: dict[str, float]         # nome -> coeficiente
    std_errors: dict[str, float]
    p_values: dict[str, float]
    rho: float | None                # parâmetro autorregressivo em Y (SAR/SDM)
    lam: float | None                # parâmetro autorregressivo nos erros (SEM)
    sigma2: float                    # variância dos erros ML
    log_likelihood: float
    aic: float
    bic: float
    n: int
    k: int                           # número de parâmetros (incl. rho/lam/sigma2)
    converged: bool
    iterations: int
    residuals: np.ndarray
    fitted: np.ndarray
    y: np.ndarray
    x: np.ndarray
    w: np.ndarray                    # matriz W densa
    feature_names: list[str]
    # Para SLX / SDM
    lag_feature_names: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------

def _build_design(
    data: pd.DataFrame,
    spec: SpatialModelSpec,
    w: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, list[str], np.ndarray, list[str]]:
    """Retorna (y, X, feature_names, WX, lag_feature_names)."""
    y = data[spec.target].astype(float).to_numpy()
    x_df = data[list(spec.predictors)].astype(float)
    if spec.add_constant:
        x_df = sm.add_constant(x_df, has_constant="add")
    x = x_df.to_numpy()
    feature_names = list(x_df.columns)

    # Lags espaciais das covariadas (SLX, SDM)
    lag_cols: list[str] = []
    wx_parts: list[np.ndarray] = []
    cols_to_lag = list(spec.lag_predictors) if spec.lag_predictors else list(spec.predictors)
    if spec.model_type in {"SLX", "SDM"}:
        raw_df = data[list(spec.predictors)].astype(float)
        for col in cols_to_lag:
            if col in raw_df.columns:
                wx_col = w @ raw_df[col].to_numpy()
                wx_parts.append(wx_col)
                lag_cols.append(f"W.{col}")
        if wx_parts:
            wx_matrix = np.column_stack(wx_parts)
        else:
            wx_matrix = np.empty((len(y), 0))
        # Para SLX/SDM incluímos WX em X
        if wx_matrix.shape[1] > 0:
            x = np.column_stack([x, wx_matrix])
            feature_names = feature_names + lag_cols
    else:
        wx_matrix = np.empty((len(y), 0))

    return y, x, feature_names, wx_matrix, lag_cols


def _ols_estimate(y: np.ndarray, x: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray, float]:
    """OLS: retorna (beta, residuals, fitted, sigma2_ml)."""
    xtx_inv = np.linalg.pinv(x.T @ x)
    beta = xtx_inv @ x.T @ y
    fitted = x @ beta
    resid = y - fitted
    sigma2 = float(resid @ resid) / len(y)
    return beta, resid, fitted, sigma2


def _log_likelihood(n: int, sigma2: float, log_det_a: float) -> float:
    """Log-verossimilhança espacial = log_det_a - n/2 * log(sigma2) - n/2 * (1+log(2π))."""
    if sigma2 <= 0:
        return -np.inf
    return float(log_det_a - n / 2.0 * np.log(sigma2) - n / 2.0 * (1.0 + np.log(2.0 * np.pi)))


def _eigenvalues_w(w: np.ndarray) -> np.ndarray:
    """Autovalores reais da matriz W (simétrica ou não)."""
    eigs = np.linalg.eigvals(w)
    return np.real(eigs)


def _rho_bounds(eigs: np.ndarray) -> tuple[float, float]:
    e_min = float(eigs.min())
    e_max = float(eigs.max())
    eps = 1e-6
    lo = 1.0 / e_min + eps if e_min < 0 else -1.0 + eps
    hi = 1.0 / e_max - eps if e_max > 0 else 1.0 - eps
    return lo, hi


# ---------------------------------------------------------------------------
# OLS
# ---------------------------------------------------------------------------

def _fit_ols(y: np.ndarray, x: np.ndarray, spec: SpatialModelSpec, w: np.ndarray,
             feature_names: list[str]) -> dict[str, Any]:
    beta, resid, fitted, sigma2 = _ols_estimate(y, x)
    n, k = x.shape
    xtx_inv = np.linalg.pinv(x.T @ x)
    cov = sigma2 * xtx_inv * (n / (n - k))  # OLS variância não-viesada
    se = np.sqrt(np.diag(cov))
    from scipy import stats
    t_stats = beta / se
    p_vals = 2.0 * stats.t.sf(np.abs(t_stats), df=n - k)
    ll = _log_likelihood(n, sigma2, 0.0)
    aic = -2 * ll + 2 * (k + 1)
    bic = -2 * ll + np.log(n) * (k + 1)
    return dict(beta=beta, se=se, p_vals=p_vals, resid=resid, fitted=fitted,
                sigma2=sigma2, ll=ll, aic=aic, bic=bic, converged=True, iterations=0,
                rho=None, lam=None)


# ---------------------------------------------------------------------------
# SAR — Spatial Autoregressive Model
# Likelihood concentrada: β e σ² são funções analíticas de ρ.
# ---------------------------------------------------------------------------

def _fit_sar(y: np.ndarray, x: np.ndarray, spec: SpatialModelSpec, w: np.ndarray,
             feature_names: list[str]) -> dict[str, Any]:
    n = len(y)
    eigs = _eigenvalues_w(w)
    lo, hi = _rho_bounds(eigs)
    wy = w @ y

    def neg_loglik(rho: float) -> float:
        a = y - rho * wy
        beta, _, _, sigma2 = _ols_estimate(a, x)
        log_det = float(np.sum(np.log(np.abs(1.0 - rho * eigs))))
        return -(log_det - n / 2.0 * np.log(sigma2))

    result = optimize.minimize_scalar(neg_loglik, bounds=(lo, hi), method="bounded",
                                      options={"xatol": spec.tol, "maxiter": spec.max_iter})
    rho = float(result.x)
    converged = result.success
    a = y - rho * wy
    beta, _, _, sigma2 = _ols_estimate(a, x)
    fitted = rho * wy + x @ beta
    resid = y - fitted

    # Assintótica: Cov(β) ≈ σ² (X'X)⁻¹  para SAR (aproximação válida sob n grande)
    xtx_inv = np.linalg.pinv(x.T @ x)
    cov_beta = sigma2 * xtx_inv
    se_beta = np.sqrt(np.diag(cov_beta))

    # Erro padrão de ρ via 2ª derivada numérica
    h = 1e-5
    d2 = (neg_loglik(rho + h) - 2 * neg_loglik(rho) + neg_loglik(rho - h)) / h ** 2
    se_rho = float(1.0 / np.sqrt(max(d2, 1e-15)))

    from scipy import stats
    beta_p = 2.0 * stats.norm.sf(np.abs(beta / np.maximum(se_beta, 1e-15)))
    rho_p = float(2.0 * stats.norm.sf(abs(rho) / se_rho))

    log_det = float(np.sum(np.log(np.abs(1.0 - rho * eigs))))
    ll = _log_likelihood(n, sigma2, log_det)
    k = x.shape[1] + 2  # β + ρ + σ²
    aic = -2 * ll + 2 * k
    bic = -2 * ll + np.log(n) * k
    return dict(beta=beta, se=np.append(se_beta, se_rho),
                p_vals=np.append(beta_p, rho_p),
                resid=resid, fitted=fitted, sigma2=sigma2,
                ll=ll, aic=aic, bic=bic,
                converged=converged, iterations=int(getattr(result, "nit", 0)),
                rho=rho, lam=None)


# ---------------------------------------------------------------------------
# SEM — Spatial Error Model
# ---------------------------------------------------------------------------

def _fit_sem(y: np.ndarray, x: np.ndarray, spec: SpatialModelSpec, w: np.ndarray,
             feature_names: list[str]) -> dict[str, Any]:
    n = len(y)
    eigs = _eigenvalues_w(w)
    lo, hi = _rho_bounds(eigs)

    def neg_loglik(lam: float) -> float:
        b = y - lam * (w @ y)
        a = x - lam * (w @ x)
        _, _, _, sigma2 = _ols_estimate(b, a)
        log_det = float(np.sum(np.log(np.abs(1.0 - lam * eigs))))
        return -(log_det - n / 2.0 * np.log(sigma2))

    result = optimize.minimize_scalar(neg_loglik, bounds=(lo, hi), method="bounded",
                                      options={"xatol": spec.tol, "maxiter": spec.max_iter})
    lam = float(result.x)
    converged = result.success
    b = y - lam * (w @ y)
    a = x - lam * (w @ x)
    beta, _, _, sigma2 = _ols_estimate(b, a)
    fitted = x @ beta
    resid = y - fitted  # resíduos não-filtrados, padrão em SEM

    xtx_inv = np.linalg.pinv(a.T @ a)
    cov_beta = sigma2 * xtx_inv
    se_beta = np.sqrt(np.diag(cov_beta))

    h = 1e-5
    d2 = (neg_loglik(lam + h) - 2 * neg_loglik(lam) + neg_loglik(lam - h)) / h ** 2
    se_lam = float(1.0 / np.sqrt(max(d2, 1e-15)))

    from scipy import stats
    beta_p = 2.0 * stats.norm.sf(np.abs(beta / np.maximum(se_beta, 1e-15)))
    lam_p = float(2.0 * stats.norm.sf(abs(lam) / se_lam))

    log_det = float(np.sum(np.log(np.abs(1.0 - lam * eigs))))
    ll = _log_likelihood(n, sigma2, log_det)
    k = x.shape[1] + 2
    aic = -2 * ll + 2 * k
    bic = -2 * ll + np.log(n) * k
    return dict(beta=beta, se=np.append(se_beta, se_lam),
                p_vals=np.append(beta_p, lam_p),
                resid=resid, fitted=fitted, sigma2=sigma2,
                ll=ll, aic=aic, bic=bic,
                converged=converged, iterations=int(getattr(result, "nit", 0)),
                rho=None, lam=lam)


# ---------------------------------------------------------------------------
# SLX — Spatial Lag of X (OLS com variáveis WX adicionadas)
# ---------------------------------------------------------------------------

def _fit_slx(y: np.ndarray, x: np.ndarray, spec: SpatialModelSpec, w: np.ndarray,
             feature_names: list[str]) -> dict[str, Any]:
    # X já inclui WX (adicionado em _build_design)
    result = _fit_ols(y, x, spec, w, feature_names)
    return result


# ---------------------------------------------------------------------------
# SDM — Spatial Durbin Model
# ---------------------------------------------------------------------------

def _fit_sdm(y: np.ndarray, x: np.ndarray, spec: SpatialModelSpec, w: np.ndarray,
             feature_names: list[str]) -> dict[str, Any]:
    # X já inclui WX; estima-se SAR sobre esse X aumentado
    return _fit_sar(y, x, spec, w, feature_names)


# ---------------------------------------------------------------------------
# Tabela de coeficientes
# ---------------------------------------------------------------------------

def _coefficient_table(
    result: SpatialModelResult,
) -> pd.DataFrame:
    names = list(result.feature_names)
    betas = np.array([result.params[n] for n in names])
    ses = np.array([result.std_errors[n] for n in names])
    pvs = np.array([result.p_values[n] for n in names])

    extra_rows: list[dict] = []
    if result.rho is not None:
        extra_rows.append({"term": "rho", "coefficient": result.rho,
                           "std_error": result.std_errors.get("rho", float("nan")),
                           "p_value": result.p_values.get("rho", float("nan"))})
    if result.lam is not None:
        extra_rows.append({"term": "lambda", "coefficient": result.lam,
                           "std_error": result.std_errors.get("lambda", float("nan")),
                           "p_value": result.p_values.get("lambda", float("nan"))})

    rows = [
        {"model": result.spec.name, "term": n, "coefficient": float(b),
         "std_error": float(s), "p_value": float(p)}
        for n, b, s, p in zip(names, betas, ses, pvs)
    ]
    for r in extra_rows:
        rows.append({"model": result.spec.name, **r})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Ponto de entrada principal
# ---------------------------------------------------------------------------

def fit_spatial_model(
    data: pd.DataFrame,
    spec: SpatialModelSpec,
    weights: WeightMatrix,
) -> SpatialModelResult:
    """Estima o modelo espacial especificado e retorna SpatialModelResult."""
    w = weights.to_dense()
    y, x, feature_names, wx_matrix, lag_names = _build_design(data, spec, w)
    n, k_x = x.shape

    dispatchers = {
        "OLS": _fit_ols,
        "SAR": _fit_sar,
        "SEM": _fit_sem,
        "SLX": _fit_slx,
        "SDM": _fit_sdm,
    }
    fn = dispatchers[spec.model_type]
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        try:
            raw = fn(y, x, spec, w, feature_names)
        except Exception as exc:
            raise EstimationError(f"Falha na estimação {spec.model_type} '{spec.name}': {exc}") from exc

    beta = raw["beta"]
    se_full = raw["se"]
    pv_full = raw["p_vals"]

    # Organiza dicionários de parâmetros
    k_beta = len(beta)
    params: dict[str, float] = {feature_names[i]: float(beta[i]) for i in range(k_beta)}
    std_errors: dict[str, float] = {feature_names[i]: float(se_full[i]) for i in range(k_beta)}
    p_values: dict[str, float] = {feature_names[i]: float(pv_full[i]) for i in range(k_beta)}

    if raw["rho"] is not None and len(se_full) > k_beta:
        std_errors["rho"] = float(se_full[k_beta])
        p_values["rho"] = float(pv_full[k_beta])
    if raw["lam"] is not None and len(se_full) > k_beta:
        std_errors["lambda"] = float(se_full[k_beta])
        p_values["lambda"] = float(pv_full[k_beta])

    k_total = k_beta + (1 if raw["rho"] is not None else 0) + (1 if raw["lam"] is not None else 0) + 1  # +σ²

    return SpatialModelResult(
        spec=spec,
        model_type=spec.model_type,
        params=params,
        std_errors=std_errors,
        p_values=p_values,
        rho=raw["rho"],
        lam=raw["lam"],
        sigma2=float(raw["sigma2"]),
        log_likelihood=float(raw["ll"]),
        aic=float(raw["aic"]),
        bic=float(raw["bic"]),
        n=n,
        k=k_total,
        converged=bool(raw["converged"]),
        iterations=int(raw["iterations"]),
        residuals=np.asarray(raw["resid"], dtype=float),
        fitted=np.asarray(raw["fitted"], dtype=float),
        y=y,
        x=x,
        w=w,
        feature_names=feature_names,
        lag_feature_names=lag_names,
    )


def coefficient_table(result: SpatialModelResult) -> pd.DataFrame:
    return _coefficient_table(result)


def model_summary(result: SpatialModelResult) -> dict[str, Any]:
    resid = result.residuals
    rmse = float(np.sqrt(np.mean(resid ** 2)))
    ss_res = float(np.sum(resid ** 2))
    ss_tot = float(np.sum((result.y - result.y.mean()) ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan")
    return {
        "model": result.spec.name,
        "model_type": result.model_type,
        "n": result.n,
        "k": result.k,
        "rho": result.rho,
        "lambda": result.lam,
        "sigma2": result.sigma2,
        "log_likelihood": result.log_likelihood,
        "aic": result.aic,
        "bic": result.bic,
        "r_squared": r2,
        "rmse": rmse,
        "converged": result.converged,
        "iterations": result.iterations,
    }
