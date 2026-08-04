"""Gera dados sintéticos com parâmetros conhecidos para validação.

Grade 5×5, SAR com ρ=0.4, β=[2.0, 1.5, -0.8], σ²=1.0.
Parâmetros armazenados em data/demo/parametros_verdadeiros.json.
"""
from __future__ import annotations

import json
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from scipy import sparse
from shapely.geometry import box

SEED = 20260001
N_GRID = 5          # grade N_GRID × N_GRID
RHO_TRUE = 0.4
BETA_TRUE = np.array([2.0, 1.5, -0.8])  # const, x1, x2
SIGMA_TRUE = 1.0

OUTPUT = Path(__file__).parent.parent / "data" / "demo"
OUTPUT.mkdir(parents=True, exist_ok=True)


def build_rook_weights(n: int, grid_size: int) -> sparse.csr_matrix:
    rows, cols = [], []
    for r in range(grid_size):
        for c in range(grid_size):
            i = r * grid_size + c
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < grid_size and 0 <= nc < grid_size:
                    j = nr * grid_size + nc
                    rows.append(i)
                    cols.append(j)
    w = sparse.coo_matrix((np.ones(len(rows)), (rows, cols)), shape=(n, n)).tocsr()
    # Row-standardize
    row_sums = np.asarray(w.sum(axis=1)).ravel()
    inv = np.where(row_sums > 0, 1.0 / row_sums, 0.0)
    w = sparse.diags(inv) @ w
    return w.tocsr()


def simulate_sar(w: sparse.csr_matrix, rng: np.random.Generator) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    n = w.shape[0]
    x1 = rng.standard_normal(n)
    x2 = rng.uniform(-1, 1, n)
    x = np.column_stack([np.ones(n), x1, x2])
    eps = rng.normal(0, SIGMA_TRUE, n)
    w_dense = w.toarray()
    # y = (I - ρW)⁻¹ (Xβ + ε)
    a = np.eye(n) - RHO_TRUE * w_dense
    xb = x @ BETA_TRUE + eps
    y = np.linalg.solve(a, xb)
    return y, x1, x2


def main() -> None:
    rng = np.random.default_rng(SEED)
    n = N_GRID * N_GRID
    w = build_rook_weights(n, N_GRID)
    y, x1, x2 = simulate_sar(w, rng)

    ids = [f"R{r}C{c}" for r in range(N_GRID) for c in range(N_GRID)]
    geometries = [
        box(c, N_GRID - r - 1, c + 1, N_GRID - r)
        for r in range(N_GRID)
        for c in range(N_GRID)
    ]

    gdf = gpd.GeoDataFrame(
        {"id": ids, "y": y, "x1": x1, "x2": x2, "geometry": geometries},
        crs="EPSG:3857",
    )
    gpkg = OUTPUT / "demo.gpkg"
    gdf.to_file(gpkg, layer="dados", driver="GPKG")
    print(f"GeoPackage: {gpkg}")

    # Pesos rook CSV
    rows, cols = w.nonzero()
    edges = pd.DataFrame({"origin_id": [ids[r] for r in rows],
                           "destination_id": [ids[c] for c in cols],
                           "weight": w.data})
    weights_path = OUTPUT / "pesos_rook.csv"
    edges.to_csv(weights_path, index=False)
    print(f"Pesos: {weights_path}")

    # Parâmetros verdadeiros
    params = {
        "rho_true": RHO_TRUE,
        "beta_const": float(BETA_TRUE[0]),
        "beta_x1": float(BETA_TRUE[1]),
        "beta_x2": float(BETA_TRUE[2]),
        "sigma_true": SIGMA_TRUE,
        "seed": SEED,
        "n": n,
    }
    (OUTPUT / "parametros_verdadeiros.json").write_text(
        json.dumps(params, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print("Parâmetros verdadeiros salvos.")


if __name__ == "__main__":
    main()
