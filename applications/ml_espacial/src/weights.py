from __future__ import annotations

import numpy as np
from sklearn.neighbors import NearestNeighbors


def knn_weight_matrix(
    coordinates: np.ndarray,
    k: int = 8,
    weighting: str = "uniform",
    distance_power: float = 1.0,
) -> np.ndarray:
    coords = np.asarray(coordinates, dtype=float)
    n = len(coords)
    if n < 3:
        raise ValueError("spatial weights require at least 3 observations")
    k_eff = min(k + 1, n)
    nn = NearestNeighbors(n_neighbors=k_eff).fit(coords)
    distances, indices = nn.kneighbors(coords)
    distances = distances[:, 1:]
    indices = indices[:, 1:]
    w = np.zeros((n, n), dtype=float)
    rows = np.repeat(np.arange(n), indices.shape[1])
    if weighting == "uniform":
        values = np.ones(indices.size, dtype=float)
    elif weighting == "inverse_distance":
        values = 1.0 / np.maximum(distances.ravel(), 1e-12) ** distance_power
    else:
        raise ValueError(f"unknown weighting: {weighting}")
    w[rows, indices.ravel()] = values
    row_sums = w.sum(axis=1, keepdims=True)
    row_sums[row_sums == 0] = 1.0
    return w / row_sums


def cross_knn_weights(
    reference_coordinates: np.ndarray,
    query_coordinates: np.ndarray,
    k: int = 8,
    weighting: str = "uniform",
    distance_power: float = 1.0,
) -> tuple[np.ndarray, np.ndarray]:
    reference = np.asarray(reference_coordinates, dtype=float)
    query = np.asarray(query_coordinates, dtype=float)
    k_eff = min(k, len(reference))
    if k_eff < 1:
        raise ValueError("reference set is empty")
    nn = NearestNeighbors(n_neighbors=k_eff).fit(reference)
    distances, indices = nn.kneighbors(query)
    if weighting == "uniform":
        weights = np.ones_like(distances)
    elif weighting == "inverse_distance":
        weights = 1.0 / np.maximum(distances, 1e-12) ** distance_power
    else:
        raise ValueError(f"unknown weighting: {weighting}")
    weights = weights / weights.sum(axis=1, keepdims=True)
    return indices, weights
