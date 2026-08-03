from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.regression.linear_model import RegressionResultsWrapper
from statsmodels.stats.outliers_influence import variance_inflation_factor

from .config import ModelSpec


@dataclass(frozen=True)
class FittedModel:
    spec: ModelSpec
    conventional: RegressionResultsWrapper
    robust: RegressionResultsWrapper
    design: pd.DataFrame
    target: pd.Series


def build_design(data: pd.DataFrame, spec: ModelSpec) -> tuple[pd.Series, pd.DataFrame]:
    y = data[spec.target].astype(float)
    x = data[list(spec.predictors)].astype(float)
    if spec.add_constant:
        x = sm.add_constant(x, has_constant="add")
    return y, x


def fit_model(data: pd.DataFrame, spec: ModelSpec) -> FittedModel:
    y, x = build_design(data, spec)
    conventional = sm.OLS(y, x).fit()
    robust = conventional.get_robustcov_results(cov_type=spec.robust_covariance)
    return FittedModel(spec=spec, conventional=conventional, robust=robust, design=x, target=y)


def coefficient_table(model: FittedModel) -> pd.DataFrame:
    names = list(model.design.columns)
    conventional = model.conventional
    robust = model.robust
    return pd.DataFrame(
        {
            "model": model.spec.name,
            "term": names,
            "coefficient": conventional.params.to_numpy(),
            "std_error": conventional.bse.to_numpy(),
            "p_value": conventional.pvalues.to_numpy(),
            "robust_covariance": model.spec.robust_covariance,
            "robust_std_error": np.asarray(robust.bse),
            "robust_p_value": np.asarray(robust.pvalues),
            "ci_low": conventional.conf_int().iloc[:, 0].to_numpy(),
            "ci_high": conventional.conf_int().iloc[:, 1].to_numpy(),
            "robust_ci_low": np.asarray(robust.conf_int())[:, 0],
            "robust_ci_high": np.asarray(robust.conf_int())[:, 1],
        }
    )


def vif_table(model: FittedModel) -> pd.DataFrame:
    x = model.design
    rows: list[dict[str, float | str]] = []
    for idx, name in enumerate(x.columns):
        if name == "const":
            continue
        rows.append(
            {
                "model": model.spec.name,
                "term": name,
                "vif": float(variance_inflation_factor(x.to_numpy(), idx)),
            }
        )
    return pd.DataFrame(rows)


def model_summary(model: FittedModel) -> dict[str, float | int | str]:
    result = model.conventional
    return {
        "model": model.spec.name,
        "n": int(result.nobs),
        "parameters": int(result.df_model + 1),
        "r_squared": float(result.rsquared),
        "adjusted_r_squared": float(result.rsquared_adj),
        "aic": float(result.aic),
        "bic": float(result.bic),
        "rmse": float(np.sqrt(np.mean(np.square(result.resid)))),
        "condition_number": float(result.condition_number),
    }
