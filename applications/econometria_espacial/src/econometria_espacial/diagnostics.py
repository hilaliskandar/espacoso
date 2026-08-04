"""Diagnósticos pós-estimação para modelos espaciais.

Inclui:
- I de Moran nos resíduos (com permutação)
- Comparação de ajuste (AIC, BIC, log-verossimilhança)
- Verificação numérica dos impactos (direto + indireto = total)
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from .impacts import ImpactDecomposition, compute_impacts
from .models import SpatialModelResult
from .weights import WeightMatrix


def moran_i(values: np.ndarray, weights: WeightMatrix) -> float:
    x = np.asarray(values, dtype=float)
    z = x - x.mean()
    denominator = float(z @ z)
    if denominator <= 0 or weights.s0 <= 0:
        return float("nan")
    numerator = float(z @ (weights.matrix @ z))
    return float(weights.n / weights.s0 * numerator / denominator)


def moran_permutation(
    values: np.ndarray,
    weights: WeightMatrix,
    permutations: int,
    seed: int,
) -> tuple[float, float]:
    observed = moran_i(values, weights)
    if not np.isfinite(observed):
        return observed, float("nan")
    rng = np.random.default_rng(seed)
    simulated = np.empty(permutations, dtype=float)
    values = np.asarray(values, dtype=float)
    for i in range(permutations):
        simulated[i] = moran_i(rng.permutation(values), weights)
    center = float(np.mean(simulated))
    extreme = np.abs(simulated - center) >= abs(observed - center)
    p_value = (int(extreme.sum()) + 1) / (permutations + 1)
    return observed, float(p_value)


def residual_diagnostics(
    result: SpatialModelResult,
    weights: WeightMatrix,
    permutations: int,
    seed: int,
) -> dict[str, float | str | int]:
    resid = result.residuals
    moran, moran_p = moran_permutation(resid, weights, permutations=permutations, seed=seed)
    jb_result = stats.jarque_bera(resid)
    jb = float(jb_result.statistic)
    jb_p = float(jb_result.pvalue)
    skew = float(stats.skew(resid))
    kurt = float(stats.kurtosis(resid))
    return {
        "model": result.spec.name,
        "model_type": result.model_type,
        "weights": weights.name,
        "moran_residual": float(moran),
        "moran_residual_p": float(moran_p),
        "jarque_bera": float(jb),
        "jarque_bera_p": float(jb_p),
        "residual_skew": float(skew),
        "residual_kurtosis": float(kurt),
        "residual_mean": float(resid.mean()),
        "residual_std": float(resid.std()),
    }


def fit_comparison(results: list[SpatialModelResult]) -> pd.DataFrame:
    """Tabela comparativa de ajuste entre modelos."""
    rows: list[dict] = []
    for r in results:
        resid = r.residuals
        ss_res = float(np.sum(resid ** 2))
        ss_tot = float(np.sum((r.y - r.y.mean()) ** 2))
        r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan")
        rows.append({
            "model": r.spec.name,
            "model_type": r.model_type,
            "n": r.n,
            "k": r.k,
            "log_likelihood": r.log_likelihood,
            "aic": r.aic,
            "bic": r.bic,
            "r_squared": r2,
            "rmse": float(np.sqrt(np.mean(resid ** 2))),
            "converged": r.converged,
        })
    return pd.DataFrame(rows)


def verify_impacts_numerically(decomps: list[ImpactDecomposition], tol: float = 1e-8) -> pd.DataFrame:
    """Verifica numericamente que direto + indireto ≈ total."""
    rows: list[dict] = []
    for d in decomps:
        diff = abs(d.direct + d.indirect - d.total)
        rows.append({
            "model": d.model,
            "term": d.term,
            "direct": d.direct,
            "indirect": d.indirect,
            "total": d.total,
            "direct_plus_indirect": d.direct + d.indirect,
            "numerical_error": diff,
            "ok": diff <= tol,
        })
    return pd.DataFrame(rows)
