from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.diagnostic import het_breuschpagan, het_white
from statsmodels.stats.stattools import durbin_watson, jarque_bera

from .modeling import FittedModel
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


def lm_tests(model: FittedModel, weights: WeightMatrix) -> dict[str, float]:
    """Testes LM clássicos e robustos segundo a formulação de Anselin.

    A função usa variância ML (u'u / n), como nas estatísticas LM usuais.
    """
    u = np.asarray(model.conventional.resid, dtype=float).reshape(-1, 1)
    y = np.asarray(model.target, dtype=float).reshape(-1, 1)
    x = np.asarray(model.design, dtype=float)
    beta = np.asarray(model.conventional.params, dtype=float).reshape(-1, 1)
    w = weights.matrix.toarray()
    n = len(u)
    sigma2 = float((u.T @ u).item() / n)
    if sigma2 <= 0:
        return {key: float("nan") for key in [
            "lm_error", "lm_error_p", "lm_lag", "lm_lag_p",
            "robust_lm_error", "robust_lm_error_p",
            "robust_lm_lag", "robust_lm_lag_p", "lm_sarma", "lm_sarma_p",
        ]}

    utwu = float((u.T @ w @ u).item() / sigma2)
    utwy = float((u.T @ w @ y).item() / sigma2)
    t_value = float(np.trace((w.T + w) @ w))

    wxb = w @ x @ beta
    xtx_inv = np.linalg.pinv(x.T @ x)
    m = np.eye(n) - x @ xtx_inv @ x.T
    j_value = float((wxb.T @ m @ wxb).item() / sigma2 + t_value)

    lm_error = utwu**2 / t_value if t_value > 0 else float("nan")
    lm_lag = utwy**2 / j_value if j_value > 0 else float("nan")
    rlm_error_den = t_value * (1.0 - t_value / j_value) if j_value > 0 else float("nan")
    robust_lm_error = (
        (utwu - (t_value / j_value) * utwy) ** 2 / rlm_error_den
        if np.isfinite(rlm_error_den) and rlm_error_den > 0
        else float("nan")
    )
    robust_lm_lag = (
        (utwy - utwu) ** 2 / (j_value - t_value)
        if j_value - t_value > 0
        else float("nan")
    )
    lm_sarma = lm_error + robust_lm_lag if np.isfinite(lm_error + robust_lm_lag) else float("nan")

    def p1(value: float) -> float:
        return float(stats.chi2.sf(value, 1)) if np.isfinite(value) else float("nan")

    return {
        "lm_error": float(lm_error),
        "lm_error_p": p1(lm_error),
        "lm_lag": float(lm_lag),
        "lm_lag_p": p1(lm_lag),
        "robust_lm_error": float(robust_lm_error),
        "robust_lm_error_p": p1(robust_lm_error),
        "robust_lm_lag": float(robust_lm_lag),
        "robust_lm_lag_p": p1(robust_lm_lag),
        "lm_sarma": float(lm_sarma),
        "lm_sarma_p": float(stats.chi2.sf(lm_sarma, 2)) if np.isfinite(lm_sarma) else float("nan"),
    }


def classical_diagnostics(model: FittedModel) -> dict[str, float | str]:
    result = model.conventional
    residuals = np.asarray(result.resid, dtype=float)
    exog = np.asarray(model.design, dtype=float)
    bp_lm, bp_lm_p, bp_f, bp_f_p = het_breuschpagan(residuals, exog)
    try:
        white_lm, white_lm_p, white_f, white_f_p = het_white(residuals, exog)
    except AssertionError:
        white_lm = white_lm_p = white_f = white_f_p = float("nan")
    jb, jb_p, skew, kurtosis = jarque_bera(residuals)
    return {
        "model": model.spec.name,
        "durbin_watson": float(durbin_watson(residuals)),
        "breusch_pagan_lm": float(bp_lm),
        "breusch_pagan_lm_p": float(bp_lm_p),
        "breusch_pagan_f": float(bp_f),
        "breusch_pagan_f_p": float(bp_f_p),
        "white_lm": float(white_lm),
        "white_lm_p": float(white_lm_p),
        "white_f": float(white_f),
        "white_f_p": float(white_f_p),
        "jarque_bera": float(jb),
        "jarque_bera_p": float(jb_p),
        "residual_skew": float(skew),
        "residual_kurtosis": float(kurtosis),
    }


def influence_table(model: FittedModel, ids: list[str]) -> pd.DataFrame:
    influence = model.conventional.get_influence()
    frame = influence.summary_frame()
    return pd.DataFrame(
        {
            "model": model.spec.name,
            "id": ids,
            "fitted": np.asarray(model.conventional.fittedvalues),
            "residual": np.asarray(model.conventional.resid),
            "standardized_residual": frame["standard_resid"].to_numpy(),
            "studentized_residual": frame["student_resid"].to_numpy(),
            "leverage": frame["hat_diag"].to_numpy(),
            "cooks_distance": frame["cooks_d"].to_numpy(),
            "dffits": frame["dffits_internal"].to_numpy(),
        }
    )


def spatial_diagnostics(
    model: FittedModel,
    weights: WeightMatrix,
    permutations: int,
    seed: int,
) -> dict[str, float | int | str]:
    moran, moran_p = moran_permutation(
        np.asarray(model.conventional.resid),
        weights,
        permutations=permutations,
        seed=seed,
    )
    lm = lm_tests(model, weights)
    return {
        "model": model.spec.name,
        "weights": weights.name,
        "moran_residual": moran,
        "moran_residual_p": moran_p,
        "islands": len(weights.islands),
        **lm,
    }
