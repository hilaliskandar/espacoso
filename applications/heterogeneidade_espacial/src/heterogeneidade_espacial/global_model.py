from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.regression.linear_model import RegressionResultsWrapper
from statsmodels.stats.outliers_influence import variance_inflation_factor

from .config import AnalysisConfig


@dataclass(frozen=True)
class GlobalResult:
    params: np.ndarray
    std_errors: np.ndarray
    t_values: np.ndarray
    p_values: np.ndarray
    ci_low: np.ndarray
    ci_high: np.ndarray
    fitted: np.ndarray
    residuals: np.ndarray
    r_squared: float
    adj_r_squared: float
    aic: float
    bic: float
    rmse: float
    condition_number: float
    feature_names: list[str]
    result: RegressionResultsWrapper


def fit_global(
    y: np.ndarray,
    x: np.ndarray,
    feature_names: list[str],
    robust_covariance: str = "HC3",
) -> GlobalResult:
    ols = sm.OLS(y, x).fit()
    robust = ols.get_robustcov_results(cov_type=robust_covariance)
    ci = np.asarray(ols.conf_int())
    return GlobalResult(
        params=np.asarray(ols.params),
        std_errors=np.asarray(ols.bse),
        t_values=np.asarray(ols.tvalues),
        p_values=np.asarray(ols.pvalues),
        ci_low=ci[:, 0],
        ci_high=ci[:, 1],
        fitted=np.asarray(ols.fittedvalues),
        residuals=np.asarray(ols.resid),
        r_squared=float(ols.rsquared),
        adj_r_squared=float(ols.rsquared_adj),
        aic=float(ols.aic),
        bic=float(ols.bic),
        rmse=float(np.sqrt(np.mean(np.square(ols.resid)))),
        condition_number=float(ols.condition_number),
        feature_names=feature_names,
        result=ols,
    )


def global_coefficient_table(res: GlobalResult) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "model": "OLS_global",
            "term": res.feature_names,
            "coefficient": res.params,
            "std_error": res.std_errors,
            "t_value": res.t_values,
            "p_value": res.p_values,
            "ci_low": res.ci_low,
            "ci_high": res.ci_high,
        }
    )


def global_summary(res: GlobalResult) -> dict:
    return {
        "model": "OLS_global",
        "n": int(res.result.nobs),
        "parameters": int(res.result.df_model + 1),
        "r_squared": res.r_squared,
        "adj_r_squared": res.adj_r_squared,
        "aic": res.aic,
        "bic": res.bic,
        "rmse": res.rmse,
        "condition_number": res.condition_number,
    }


def vif_table(x: np.ndarray, feature_names: list[str]) -> pd.DataFrame:
    rows = []
    for idx, name in enumerate(feature_names):
        if name == "const":
            continue
        rows.append(
            {
                "model": "OLS_global",
                "term": name,
                "vif": float(variance_inflation_factor(x, idx)),
            }
        )
    return pd.DataFrame(rows)
