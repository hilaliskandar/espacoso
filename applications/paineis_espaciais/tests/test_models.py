from __future__ import annotations

import numpy as np
import pytest

from paineis_espaciais.models import (
    compare_models,
    fit_fe,
    fit_spatial_error,
    fit_spatial_lag,
)
from paineis_espaciais.panel import build_panel
from paineis_espaciais.errors import PanelError


# ---------------------------------------------------------------------------
# fit_fe
# ---------------------------------------------------------------------------

def test_fit_fe_unit(small_panel_df):
    panel = build_panel(small_panel_df, "unit_id", "time_id")
    result = fit_fe(panel, target="y", predictors=["x1", "x2"], fixed_effects="unit")
    assert result.spec_name == "fe"
    assert result.n_obs > 0
    assert hasattr(result.result, "rsquared")


def test_fit_fe_twoway(small_panel_df):
    panel = build_panel(small_panel_df, "unit_id", "time_id")
    result = fit_fe(panel, target="y", predictors=["x1"], fixed_effects="two_way")
    assert result.fixed_effects == "two_way"


def test_fit_fe_invalid_fe(small_panel_df):
    panel = build_panel(small_panel_df, "unit_id", "time_id")
    with pytest.raises(PanelError, match="fixed_effects"):
        fit_fe(panel, target="y", predictors=["x1"], fixed_effects="invalid")


def test_fit_fe_missing_col(small_panel_df):
    panel = build_panel(small_panel_df, "unit_id", "time_id")
    with pytest.raises(PanelError, match="Colunas ausentes"):
        fit_fe(panel, target="z_nonexistent", predictors=["x1"])


# ---------------------------------------------------------------------------
# fit_spatial_lag
# ---------------------------------------------------------------------------

def test_fit_spatial_lag_returns_result(small_panel_df, W_4x4):
    panel = build_panel(small_panel_df, "unit_id", "time_id")
    result = fit_spatial_lag(
        panel, W=W_4x4, target="y", predictors=["x1", "x2"], spec_name="sl_test"
    )
    assert result.model_type == "spatial_lag"
    assert result.spatial_param_name == "rho"
    assert np.isfinite(result.rho_or_lambda)
    assert result.n_obs > 0


def test_fit_spatial_lag_r_squared_range(small_panel_df, W_4x4):
    panel = build_panel(small_panel_df, "unit_id", "time_id")
    result = fit_spatial_lag(panel, W=W_4x4, target="y", predictors=["x1"])
    # R² pode ser negativo no caso de modelo IV mal identificado, mas deve ser finito
    assert np.isfinite(result.r_squared)


def test_fit_spatial_lag_identification_note(small_panel_df, W_4x4):
    panel = build_panel(small_panel_df, "unit_id", "time_id")
    result = fit_spatial_lag(panel, W=W_4x4, target="y", predictors=["x1"])
    assert len(result.identification_note) > 0


# ---------------------------------------------------------------------------
# fit_spatial_error
# ---------------------------------------------------------------------------

def test_fit_spatial_error_returns_result(small_panel_df, W_4x4):
    panel = build_panel(small_panel_df, "unit_id", "time_id")
    result = fit_spatial_error(
        panel, W=W_4x4, target="y", predictors=["x1", "x2"], spec_name="se_test"
    )
    assert result.model_type == "spatial_error"
    assert result.spatial_param_name == "lambda"
    assert -1.0 <= result.rho_or_lambda <= 1.0


def test_fit_spatial_error_finite_params(small_panel_df, W_4x4):
    panel = build_panel(small_panel_df, "unit_id", "time_id")
    result = fit_spatial_error(panel, W=W_4x4, target="y", predictors=["x1", "x2"])
    assert np.all(np.isfinite(result.params))


# ---------------------------------------------------------------------------
# compare_models
# ---------------------------------------------------------------------------

def test_compare_models_columns(small_panel_df, W_4x4):
    panel = build_panel(small_panel_df, "unit_id", "time_id")
    fe = fit_fe(panel, target="y", predictors=["x1"])
    sl = fit_spatial_lag(panel, W=W_4x4, target="y", predictors=["x1"])
    se = fit_spatial_error(panel, W=W_4x4, target="y", predictors=["x1"])
    comparison = compare_models(fe, [sl, se])
    assert "spec_name" in comparison.columns
    assert "r_squared" in comparison.columns
    assert len(comparison) == 3
