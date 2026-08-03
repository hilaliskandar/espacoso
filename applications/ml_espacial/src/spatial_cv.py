from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from sklearn.model_selection import GroupKFold, KFold
from sklearn.neighbors import NearestNeighbors


@dataclass(frozen=True)
class ValidationDesign:
    name: str
    kind: str
    n_splits: int
    n_rows: int | None = None
    n_cols: int | None = None
    buffer_distance: float = 0.0


def make_spatial_grid_groups(
    coordinates: np.ndarray,
    n_cols: int = 5,
    n_rows: int = 5,
) -> np.ndarray:
    """Assign observations to deterministic quantile-based spatial grid cells."""
    coords = np.asarray(coordinates, dtype=float)
    if coords.ndim != 2 or coords.shape[1] != 2:
        raise ValueError("coordinates must have shape (n_samples, 2)")
    if n_cols < 2 or n_rows < 2:
        raise ValueError("n_cols and n_rows must be at least 2")

    x, y = coords[:, 0], coords[:, 1]
    x_edges = np.unique(np.quantile(x, np.linspace(0, 1, n_cols + 1)))
    y_edges = np.unique(np.quantile(y, np.linspace(0, 1, n_rows + 1)))
    if len(x_edges) < 3 or len(y_edges) < 3:
        raise ValueError("insufficient coordinate variation to build spatial blocks")

    x_bin = np.clip(np.digitize(x, x_edges[1:-1], right=False), 0, len(x_edges) - 2)
    y_bin = np.clip(np.digitize(y, y_edges[1:-1], right=False), 0, len(y_edges) - 2)
    return y_bin * (len(x_edges) - 1) + x_bin


def random_splits(n_samples: int, n_splits: int, seed: int):
    splitter = KFold(n_splits=n_splits, shuffle=True, random_state=seed)
    indices = np.arange(n_samples)
    yield from splitter.split(indices)


def spatial_splits(groups: np.ndarray, n_splits: int):
    groups = np.asarray(groups)
    unique_groups = np.unique(groups)
    if len(unique_groups) < n_splits:
        raise ValueError(
            f"need at least {n_splits} unique spatial groups, found {len(unique_groups)}"
        )
    splitter = GroupKFold(n_splits=n_splits)
    indices = np.arange(len(groups))
    yield from splitter.split(indices, groups=groups)


def apply_buffer(
    train_idx: np.ndarray,
    test_idx: np.ndarray,
    coordinates: np.ndarray,
    buffer_distance: float,
) -> np.ndarray:
    """Remove training observations within buffer_distance of any test observation."""
    if buffer_distance <= 0:
        return np.asarray(train_idx, dtype=int)
    coords = np.asarray(coordinates, dtype=float)
    test_nn = NearestNeighbors(n_neighbors=1).fit(coords[test_idx])
    distances, _ = test_nn.kneighbors(coords[train_idx])
    keep = distances[:, 0] > buffer_distance
    filtered = np.asarray(train_idx, dtype=int)[keep]
    if len(filtered) < 3:
        raise ValueError(
            "buffer removed too many training observations; reduce buffer_distance"
        )
    return filtered


def build_splits(
    coordinates: np.ndarray,
    design: ValidationDesign,
    seed: int,
):
    coords = np.asarray(coordinates, dtype=float)
    if design.kind == "random":
        yield from random_splits(len(coords), design.n_splits, seed)
        return
    if design.kind != "spatial":
        raise ValueError(f"unknown validation kind: {design.kind}")
    if design.n_rows is None or design.n_cols is None:
        raise ValueError("spatial validation requires n_rows and n_cols")
    groups = make_spatial_grid_groups(coords, design.n_cols, design.n_rows)
    for train_idx, test_idx in spatial_splits(groups, design.n_splits):
        filtered_train = apply_buffer(
            train_idx, test_idx, coords, design.buffer_distance
        )
        yield filtered_train, test_idx


def groups_for_design(coordinates: np.ndarray, design: ValidationDesign) -> np.ndarray:
    if design.kind == "random":
        return np.full(len(coordinates), -1, dtype=int)
    if design.n_rows is None or design.n_cols is None:
        raise ValueError("spatial validation requires n_rows and n_cols")
    return make_spatial_grid_groups(coordinates, design.n_cols, design.n_rows)
