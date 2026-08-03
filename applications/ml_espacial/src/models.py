from __future__ import annotations

from itertools import product
from typing import Any

import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


def build_model(model_id: str, params: dict, seed: int, n_jobs: int = -1) -> Any:
    if model_id == "M0":
        return make_pipeline(StandardScaler(), Ridge(alpha=float(params["alpha"])))
    if model_id in {"M1", "M2U", "M2D", "M3"}:
        return RandomForestRegressor(
            n_estimators=int(params["n_estimators"]),
            min_samples_leaf=int(params["min_samples_leaf"]),
            max_features=float(params["max_features"]),
            n_jobs=n_jobs,
            random_state=seed,
        )
    raise ValueError(f"unknown model_id: {model_id}")


def parameter_grid(model_id: str, cfg: dict) -> list[dict]:
    if model_id == "M0":
        return [{"alpha": value} for value in cfg["ridge"]["alpha_grid"]]
    rf = cfg["random_forest"]
    keys = ["n_estimators", "min_samples_leaf", "max_features"]
    values = [rf[f"{key}_grid"] for key in keys]
    return [dict(zip(keys, combination)) for combination in product(*values)]


def append_features(base: np.ndarray, extra: np.ndarray | None) -> np.ndarray:
    if extra is None:
        return np.asarray(base, dtype=float)
    return np.column_stack([np.asarray(base, dtype=float), np.asarray(extra, dtype=float)])
