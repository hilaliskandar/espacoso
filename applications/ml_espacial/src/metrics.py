from __future__ import annotations

import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from .weights import knn_weight_matrix


def regression_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
    return {
        "rmse": float(np.sqrt(mean_squared_error(y_true, y_pred))),
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "r2": float(r2_score(y_true, y_pred)),
    }


def interval_metrics(
    y_true: np.ndarray, lower: np.ndarray, upper: np.ndarray
) -> dict[str, float]:
    covered = (y_true >= lower) & (y_true <= upper)
    return {
        "interval_coverage": float(np.mean(covered)),
        "interval_width": float(np.mean(upper - lower)),
    }


def moran_i(
    values: np.ndarray,
    coordinates: np.ndarray,
    k: int = 8,
    weighting: str = "uniform",
    permutations: int = 199,
    seed: int = 0,
) -> tuple[float, float]:
    z = np.asarray(values, dtype=float)
    z = z - np.nanmean(z)
    w = knn_weight_matrix(coordinates, k=k, weighting=weighting)
    n = len(z)
    s0 = w.sum()
    denom = np.dot(z, z)
    if denom == 0:
        return 0.0, 1.0
    observed = float((n / s0) * (z @ w @ z) / denom)

    rng = np.random.default_rng(seed)
    permuted = np.empty(permutations, dtype=float)
    for i in range(permutations):
        zp = rng.permutation(z)
        permuted[i] = (n / s0) * (zp @ w @ zp) / np.dot(zp, zp)
    p_value = float((1 + np.sum(np.abs(permuted) >= abs(observed))) / (permutations + 1))
    return observed, p_value


def local_moran(
    values: np.ndarray,
    coordinates: np.ndarray,
    k: int = 8,
    weighting: str = "uniform",
    permutations: int = 199,
    seed: int = 0,
    alpha: float = 0.05,
) -> dict[str, np.ndarray]:
    values = np.asarray(values, dtype=float)
    z = values - np.mean(values)
    variance = np.mean(z**2)
    if variance == 0:
        n = len(values)
        return {
            "local_i": np.zeros(n),
            "local_p": np.ones(n),
            "cluster": np.full(n, "NS", dtype=object),
            "spatial_lag": np.zeros(n),
        }
    w = knn_weight_matrix(coordinates, k=k, weighting=weighting)
    lag = w @ z
    observed = z * lag / variance
    rng = np.random.default_rng(seed)
    counts = np.ones(len(z), dtype=int)
    for _ in range(permutations):
        zp = rng.permutation(z)
        simulated = zp * (w @ zp) / np.mean(zp**2)
        counts += np.abs(simulated) >= np.abs(observed)
    p_values = counts / (permutations + 1)
    cluster = np.full(len(z), "NS", dtype=object)
    significant = p_values <= alpha
    cluster[significant & (z >= 0) & (lag >= 0)] = "HH"
    cluster[significant & (z < 0) & (lag < 0)] = "LL"
    cluster[significant & (z >= 0) & (lag < 0)] = "HL"
    cluster[significant & (z < 0) & (lag >= 0)] = "LH"
    return {
        "local_i": observed,
        "local_p": p_values,
        "cluster": cluster,
        "spatial_lag": lag,
    }


def conformal_quantile(abs_residuals: np.ndarray, coverage: float) -> float:
    residuals = np.sort(np.asarray(abs_residuals, dtype=float))
    if len(residuals) == 0:
        raise ValueError("calibration residuals are empty")
    rank = int(np.ceil((len(residuals) + 1) * coverage)) - 1
    rank = min(max(rank, 0), len(residuals) - 1)
    return float(residuals[rank])
