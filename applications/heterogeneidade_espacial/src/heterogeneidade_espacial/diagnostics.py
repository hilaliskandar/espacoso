from __future__ import annotations

import numpy as np
import pandas as pd

from .global_model import GlobalResult
from .gwr_model import GWRResult


def comparison_table(global_res: GlobalResult, *local_results: GWRResult) -> pd.DataFrame:
    """Compare AIC, BIC, R² across global and local models."""
    rows = [
        {
            "model": "OLS_global",
            "aic": global_res.aic,
            "bic": global_res.bic,
            "r_squared": global_res.r_squared,
            "adj_r_squared": global_res.adj_r_squared,
            "rmse": global_res.rmse,
            "bandwidth": float("nan"),
        }
    ]
    for res in local_results:
        rows.append(
            {
                "model": res.model_name,
                "aic": res.aic,
                "bic": res.bic,
                "r_squared": res.r_squared,
                "adj_r_squared": res.adj_r_squared,
                "rmse": float(np.sqrt(np.mean(np.square(res.residuals)))),
                "bandwidth": res.bandwidth,
            }
        )
    return pd.DataFrame(rows)


def coefficient_variability(res: GWRResult) -> pd.DataFrame:
    """Per-predictor summary statistics of local coefficients."""
    rows = []
    for j, name in enumerate(res.feature_names):
        col = res.params[:, j]
        rows.append(
            {
                "model": res.model_name,
                "term": name,
                "mean": float(np.mean(col)),
                "std": float(np.std(col)),
                "min": float(np.min(col)),
                "q25": float(np.percentile(col, 25)),
                "median": float(np.median(col)),
                "q75": float(np.percentile(col, 75)),
                "max": float(np.max(col)),
                "iqr": float(np.percentile(col, 75) - np.percentile(col, 25)),
            }
        )
    return pd.DataFrame(rows)


def bootstrap_stability(
    coords: np.ndarray,
    y: np.ndarray,
    x: np.ndarray,
    feature_names: list[str],
    bandwidth: float,
    spec,
    n_bootstrap: int,
    fraction: float,
    seed: int,
) -> pd.DataFrame:
    """Resample observations and refit GWR to assess coefficient stability."""
    if n_bootstrap <= 0:
        return pd.DataFrame()

    from .gwr_model import fit_gwr

    rng = np.random.default_rng(seed)
    n = len(y)
    k = len(feature_names)
    sample_size = max(int(n * fraction), k + 2)

    all_params: list[np.ndarray] = []
    for _ in range(n_bootstrap):
        idx = rng.choice(n, size=sample_size, replace=False)
        try:
            res = fit_gwr(
                coords[idx],
                y[idx],
                x[idx],
                feature_names,
                spec,
                bandwidth=bandwidth,
            )
            # Average local coefficients per bootstrap sample
            all_params.append(res.params.mean(axis=0))
        except Exception:
            continue

    if not all_params:
        return pd.DataFrame()

    arr = np.vstack(all_params)
    rows = []
    for j, name in enumerate(feature_names):
        col = arr[:, j]
        rows.append(
            {
                "term": name,
                "bootstrap_mean": float(np.mean(col)),
                "bootstrap_std": float(np.std(col)),
                "bootstrap_ci_low": float(np.percentile(col, 2.5)),
                "bootstrap_ci_high": float(np.percentile(col, 97.5)),
                "n_successful": len(all_params),
            }
        )
    return pd.DataFrame(rows)
