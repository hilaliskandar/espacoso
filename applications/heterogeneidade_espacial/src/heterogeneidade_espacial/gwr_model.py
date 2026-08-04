from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .config import BandwidthSpec


@dataclass(frozen=True)
class GWRResult:
    """Results from a fitted GWR model."""

    model_name: str
    params: np.ndarray          # (n, k) local coefficients
    std_errors: np.ndarray      # (n, k)
    t_values: np.ndarray        # (n, k)
    p_values: np.ndarray        # (n, k)
    ci_low: np.ndarray          # (n, k)
    ci_high: np.ndarray         # (n, k)
    fitted: np.ndarray          # (n,)
    residuals: np.ndarray       # (n,)
    localr2: np.ndarray         # (n,)
    influence: np.ndarray       # (n,) hat diagonal
    bandwidth: float
    aic: float
    aicc: float
    bic: float
    r_squared: float
    adj_r_squared: float
    feature_names: list[str]


def _bandwidth_kwargs(spec: BandwidthSpec, coords: np.ndarray, y: np.ndarray, x: np.ndarray):
    """Build keyword arguments for mgwr Sel_BW."""
    kwargs: dict = {
        "criterion": spec.criterion,
        "kernel": spec.kernel,
        "fixed": spec.fixed_or_adaptive == "fixed",
        "search_method": spec.search_method,
    }
    if spec.min_bandwidth is not None:
        kwargs["bw_min"] = spec.min_bandwidth
    if spec.max_bandwidth is not None:
        kwargs["bw_max"] = spec.max_bandwidth
    return kwargs


def _bw_bounds(
    spec: BandwidthSpec,
    n: int,
    k: int,
) -> tuple[float | None, float | None]:
    """Derive safe bandwidth search bounds given dataset size."""
    adaptive = spec.fixed_or_adaptive == "adaptive"
    bw_min = spec.min_bandwidth
    bw_max = spec.max_bandwidth
    if adaptive:
        # Minimum must be > k so that local regression is identified.
        safe_min = float(k + 2)
        if bw_min is None or bw_min < safe_min:
            bw_min = safe_min
        # Maximum must be < n so that kth-neighbour lookup stays in bounds.
        safe_max = float(n - 1)
        if bw_max is None or bw_max > safe_max:
            bw_max = safe_max
    return bw_min, bw_max


def select_bandwidth(
    coords: np.ndarray,
    y: np.ndarray,
    x: np.ndarray,
    spec: BandwidthSpec,
) -> float:
    from mgwr.sel_bw import Sel_BW

    n, k = x.shape
    bw_min, bw_max = _bw_bounds(spec, n, k)
    selector = Sel_BW(
        coords,
        y.reshape(-1, 1),
        x,
        kernel=spec.kernel,
        fixed=spec.fixed_or_adaptive == "fixed",
        multi=False,
        constant=False,  # constant already in x if add_constant=True
    )
    bw = selector.search(
        criterion=spec.criterion,
        search_method=spec.search_method,
        bw_min=bw_min,
        bw_max=bw_max,
    )
    return float(bw)


def fit_gwr(
    coords: np.ndarray,
    y: np.ndarray,
    x: np.ndarray,
    feature_names: list[str],
    spec: BandwidthSpec,
    bandwidth: float | None = None,
) -> GWRResult:
    from mgwr.gwr import GWR

    if bandwidth is None:
        bandwidth = select_bandwidth(coords, y, x, spec)

    model = GWR(
        coords,
        y.reshape(-1, 1),
        x,
        bw=bandwidth,
        kernel=spec.kernel,
        fixed=spec.fixed_or_adaptive == "fixed",
        constant=False,
    )
    res = model.fit()

    n, k = res.params.shape
    alpha = 0.05
    from scipy.stats import t as t_dist

    df_resid = float(getattr(res, "df_resid", max(n - k, 1)))
    df_local = float(res.df_local.mean()) if hasattr(res, "df_local") and res.df_local is not None else df_resid
    df = max(df_local, 1)
    t_crit = float(t_dist.ppf(1 - alpha / 2, df))

    params = res.params
    se = np.asarray(res.bse) if res.bse is not None else np.full_like(params, np.nan)
    tvals = np.asarray(res.tvalues) if res.tvalues is not None else np.full_like(params, np.nan)
    # pvalues is often None in mgwr; compute from tvalues when available
    if res.pvalues is not None:
        pvals = np.asarray(res.pvalues)
    else:
        pvals = 2 * t_dist.sf(np.abs(tvals), df)
    ci_low = params - t_crit * se
    ci_high = params + t_crit * se

    fitted = np.asarray(res.predy).ravel()
    residuals = np.asarray(res.resid_response).ravel()
    localr2 = np.asarray(res.localR2).ravel() if hasattr(res, "localR2") else np.full(n, np.nan)
    influence = np.asarray(res.influ).ravel() if hasattr(res, "influ") else np.full(n, np.nan)

    return GWRResult(
        model_name="GWR",
        params=params,
        std_errors=se,
        t_values=tvals,
        p_values=pvals,
        ci_low=ci_low,
        ci_high=ci_high,
        fitted=fitted,
        residuals=residuals,
        localr2=localr2,
        influence=influence,
        bandwidth=bandwidth,
        aic=float(res.aic),
        aicc=float(res.aicc),
        bic=float(res.bic),
        r_squared=float(res.R2),
        adj_r_squared=float(res.adj_R2),
        feature_names=feature_names,
    )


def fit_mgwr(
    coords: np.ndarray,
    y: np.ndarray,
    x: np.ndarray,
    feature_names: list[str],
    spec: BandwidthSpec,
) -> GWRResult:
    from mgwr.gwr import MGWR
    from mgwr.sel_bw import Sel_BW

    selector = Sel_BW(
        coords,
        y.reshape(-1, 1),
        x,
        kernel=spec.kernel,
        fixed=spec.fixed_or_adaptive == "fixed",
        multi=True,
        constant=False,
    )
    n_obs, k = x.shape
    bw_min, bw_max = _bw_bounds(spec, n_obs, k)
    bws = selector.search(
        criterion=spec.criterion,
        search_method=spec.search_method,
        bw_min=bw_min,
        bw_max=bw_max,
    )

    model = MGWR(
        coords,
        y.reshape(-1, 1),
        x,
        selector,
        kernel=spec.kernel,
        fixed=spec.fixed_or_adaptive == "fixed",
        constant=False,
    )
    res = model.fit()

    n, k = res.params.shape
    alpha = 0.05
    from scipy.stats import t as t_dist
    enp = getattr(res, "ENP_j", None)
    df = max(float(enp.mean()) if enp is not None else 1.0, 1.0)
    t_crit = float(t_dist.ppf(1 - alpha / 2, df))

    params = res.params
    se = np.asarray(res.bse) if res.bse is not None else np.full_like(params, np.nan)
    tvals = np.asarray(res.tvalues) if res.tvalues is not None else np.full_like(params, np.nan)
    if res.pvalues is not None:
        pvals = np.asarray(res.pvalues)
    else:
        pvals = 2 * t_dist.sf(np.abs(tvals), df)
    ci_low = params - t_crit * se
    ci_high = params + t_crit * se

    fitted = np.asarray(res.predy).ravel()
    residuals = np.asarray(res.resid_response).ravel()
    localr2 = np.asarray(res.localR2).ravel() if hasattr(res, "localR2") else np.full(n, np.nan)
    influence = np.asarray(res.influ).ravel() if hasattr(res, "influ") else np.full(n, np.nan)

    # Use median bandwidth as scalar summary
    bw_summary = float(np.median(bws)) if hasattr(bws, "__len__") else float(bws)

    return GWRResult(
        model_name="MGWR",
        params=params,
        std_errors=se,
        t_values=tvals,
        p_values=pvals,
        ci_low=ci_low,
        ci_high=ci_high,
        fitted=fitted,
        residuals=residuals,
        localr2=localr2,
        influence=influence,
        bandwidth=bw_summary,
        aic=float(res.aic),
        aicc=float(res.aicc),
        bic=float(res.bic),
        r_squared=float(res.R2),
        adj_r_squared=float(res.adj_R2),
        feature_names=feature_names,
    )


def gwr_coefficient_table(res: GWRResult, ids: list[str]) -> pd.DataFrame:
    rows = []
    n = res.params.shape[0]
    for i in range(n):
        for j, name in enumerate(res.feature_names):
            rows.append(
                {
                    "model": res.model_name,
                    "id": ids[i],
                    "term": name,
                    "coefficient": float(res.params[i, j]),
                    "std_error": float(res.std_errors[i, j]),
                    "t_value": float(res.t_values[i, j]),
                    "p_value": float(res.p_values[i, j]),
                    "ci_low": float(res.ci_low[i, j]),
                    "ci_high": float(res.ci_high[i, j]),
                }
            )
    return pd.DataFrame(rows)


def gwr_summary(res: GWRResult) -> dict:
    return {
        "model": res.model_name,
        "bandwidth": res.bandwidth,
        "aic": res.aic,
        "aicc": res.aicc,
        "bic": res.bic,
        "r_squared": res.r_squared,
        "adj_r_squared": res.adj_r_squared,
    }


def local_collinearity(res: GWRResult) -> pd.DataFrame:
    """Local condition number and variance decomposition per observation."""
    rows = []
    for i in range(res.params.shape[0]):
        # Use local coefficient standard errors as proxy for collinearity
        se_row = res.std_errors[i]
        rows.append(
            {
                "obs_index": i,
                "local_coef_se_max": float(np.nanmax(se_row)),
                "local_coef_se_mean": float(np.nanmean(se_row)),
                "local_coef_cv": float(np.nanstd(se_row) / np.nanmean(se_row))
                if np.nanmean(se_row) > 0
                else float("nan"),
            }
        )
    return pd.DataFrame(rows)
