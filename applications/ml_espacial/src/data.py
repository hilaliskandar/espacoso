from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
from sklearn.datasets import fetch_california_housing


@dataclass(frozen=True)
class SpatialDataset:
    frame: pd.DataFrame
    target_column: str
    coordinate_columns: tuple[str, str]


def load_california_housing(
    sample_limit: Optional[int] = None, seed: int = 0
) -> SpatialDataset:
    """Load California Housing with coordinates and target in one DataFrame."""
    bunch = fetch_california_housing(as_frame=True)
    frame = bunch.frame.copy()
    if sample_limit is not None and sample_limit < len(frame):
        frame = frame.sample(n=sample_limit, random_state=seed).sort_index()
    return SpatialDataset(
        frame=frame.reset_index(drop=True),
        target_column="MedHouseVal",
        coordinate_columns=("Longitude", "Latitude"),
    )


def load_synthetic_spatial(n_samples: int = 600, seed: int = 0) -> SpatialDataset:
    """Create a deterministic benchmark with nonlinear and spatial structure."""
    rng = np.random.default_rng(seed)
    longitude = rng.uniform(-124.0, -114.0, n_samples)
    latitude = rng.uniform(32.0, 42.0, n_samples)
    income = rng.lognormal(mean=1.2, sigma=0.45, size=n_samples)
    house_age = rng.uniform(1, 50, n_samples)
    rooms = rng.normal(5.0, 1.2, n_samples)
    population = rng.lognormal(mean=7.0, sigma=0.5, size=n_samples)

    spatial_surface = (
        0.8 * np.sin((longitude + 119.0) * 0.9)
        + 0.6 * np.cos((latitude - 37.0) * 0.8)
        + 0.4 * np.sin((longitude + latitude) * 0.7)
    )
    nonlinear = 0.55 * np.log1p(income) + 0.05 * rooms**2 - 0.006 * house_age
    noise = rng.normal(0, 0.22, n_samples)
    target = nonlinear + spatial_surface + noise

    frame = pd.DataFrame(
        {
            "MedInc": income,
            "HouseAge": house_age,
            "AveRooms": rooms,
            "Population": population,
            "Longitude": longitude,
            "Latitude": latitude,
            "MedHouseVal": target,
        }
    )
    return SpatialDataset(
        frame=frame,
        target_column="MedHouseVal",
        coordinate_columns=("Longitude", "Latitude"),
    )


def load_csv_spatial(
    path: str | Path,
    target_column: str,
    coordinate_columns: tuple[str, str],
    sample_limit: Optional[int] = None,
    seed: int = 0,
) -> SpatialDataset:
    """Load an auditable local CSV for offline spatial experiments."""
    csv_path = Path(path)
    if not csv_path.exists():
        raise FileNotFoundError(
            f"CSV not found: {csv_path}. Place the source file at this path before running."
        )
    frame = pd.read_csv(csv_path)
    required = {target_column, *coordinate_columns}
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise ValueError(f"CSV is missing required columns: {missing}")
    numeric_cols = frame.select_dtypes(include=[np.number]).columns.tolist()
    keep = [c for c in numeric_cols if c in frame.columns]
    if target_column not in keep or any(c not in keep for c in coordinate_columns):
        raise ValueError("target and coordinate columns must be numeric")
    frame = frame[keep].dropna().copy()
    if sample_limit is not None and sample_limit < len(frame):
        frame = frame.sample(n=int(sample_limit), random_state=seed).sort_index()
    return SpatialDataset(
        frame=frame.reset_index(drop=True),
        target_column=target_column,
        coordinate_columns=coordinate_columns,
    )


def load_dataset(
    dataset_name: str, sample_limit: Optional[int], seed: int, **kwargs
) -> SpatialDataset:
    if dataset_name == "california_housing":
        return load_california_housing(sample_limit=sample_limit, seed=seed)
    if dataset_name == "local_csv":
        return load_csv_spatial(
            path=kwargs["path"],
            target_column=str(kwargs["target_column"]),
            coordinate_columns=tuple(kwargs["coordinate_columns"]),
            sample_limit=sample_limit,
            seed=seed,
        )
    if dataset_name == "synthetic_spatial":
        n_samples = int(sample_limit or 600)
        return load_synthetic_spatial(n_samples=n_samples, seed=seed)
    raise ValueError(f"unknown dataset: {dataset_name}")
