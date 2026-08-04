from __future__ import annotations

"""Painéis espaciais e dinâmica territorial — pacote principal."""

from .panel import (
    PanelData,
    build_panel,
    check_balance,
    fill_gaps,
    lag_column,
    unit_time_index,
)
from .models import (
    FittedPanel,
    SpatialPanelResult,
    fit_fe,
    fit_spatial_lag,
    fit_spatial_error,
    compare_models,
)
from .weights import build_weights, WeightSpec
from .config import load_config, PanelConfig
from .errors import PanelError

__all__ = [
    "PanelData",
    "build_panel",
    "check_balance",
    "fill_gaps",
    "lag_column",
    "unit_time_index",
    "FittedPanel",
    "SpatialPanelResult",
    "fit_fe",
    "fit_spatial_lag",
    "fit_spatial_error",
    "compare_models",
    "build_weights",
    "WeightSpec",
    "load_config",
    "PanelConfig",
    "PanelError",
]
