"""Fixtures compartilhadas para testes de econometria_espacial."""
from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import pytest
from scipy import sparse
from shapely.geometry import box


@pytest.fixture
def grid_4x1(tmp_path: Path):
    """Grade linear 4 células, pesos rook row-standardized."""
    gdf = gpd.GeoDataFrame(
        {
            "id": ["A", "B", "C", "D"],
            "x1": [0.5, 1.5, 2.5, 3.5],
            "x2": [1.0, 0.0, 1.0, 0.0],
            "y":  [1.0, 3.0, 5.0, 7.0],
            "geometry": [box(i, 0, i + 1, 1) for i in range(4)],
        },
        crs="EPSG:3857",
    )
    gpkg = tmp_path / "data.gpkg"
    gdf.to_file(gpkg, layer="dados", driver="GPKG")
    # Vizinhança: A-B, B-C, C-D (rook linear)
    edges = pd.DataFrame(
        {
            "origin_id":      ["A", "B", "B", "C", "C", "D"],
            "destination_id": ["B", "A", "C", "B", "D", "C"],
            "weight":         [1.0] * 6,
        }
    )
    weights = tmp_path / "weights.csv"
    edges.to_csv(weights, index=False)
    return gdf, gpkg, weights


@pytest.fixture
def sar_synthetic():
    """Grade 5×5 com SAR simulado (parâmetros conhecidos)."""
    rng = np.random.default_rng(42)
    n = 25
    # Constrói W rook 5×5
    rows, cols = [], []
    for r in range(5):
        for c in range(5):
            i = r * 5 + c
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < 5 and 0 <= nc < 5:
                    rows.append(i)
                    cols.append(nr * 5 + nc)
    w_bin = sparse.coo_matrix((np.ones(len(rows)), (rows, cols)), shape=(n, n)).tocsr()
    row_sums = np.asarray(w_bin.sum(axis=1)).ravel()
    inv = 1.0 / np.where(row_sums > 0, row_sums, 1.0)
    w = (sparse.diags(inv) @ w_bin).tocsr().toarray()

    rho_true = 0.4
    beta_true = np.array([2.0, 1.5, -0.8])
    x1 = rng.standard_normal(n)
    x2 = rng.uniform(-1, 1, n)
    x = np.column_stack([np.ones(n), x1, x2])
    eps = rng.normal(0, 1.0, n)
    a = np.eye(n) - rho_true * w
    y = np.linalg.solve(a, x @ beta_true + eps)

    ids = [f"R{r}C{c}" for r in range(5) for c in range(5)]
    df = pd.DataFrame({"id": ids, "y": y, "x1": x1, "x2": x2})
    return df, w, rho_true, beta_true
