"""Create a synthetic spatial dataset for the heterogeneidade_espacial demo."""
from __future__ import annotations

import argparse
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.geometry import box


def create_demo(output_dir: Path, n: int = 100, seed: int = 20260007) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(seed)

    # Create a regular grid of n cells
    side = int(np.ceil(np.sqrt(n)))
    cells = []
    ids = []
    coords_x = []
    coords_y = []
    for row in range(side):
        for col in range(side):
            if len(cells) >= n:
                break
            cells.append(box(col, row, col + 1, row + 1))
            ids.append(f"C{row:03d}{col:03d}")
            coords_x.append(col + 0.5)
            coords_y.append(row + 0.5)

    cx = np.array(coords_x)
    cy = np.array(coords_y)

    # True locally varying coefficients
    beta1 = 1.0 + 2.0 * (cx / cx.max())            # increases west→east
    beta2 = 0.5 - 1.0 * (cy / cy.max())             # decreases south→north

    x1 = rng.normal(0, 1, n)
    x2 = rng.normal(0, 1, n)
    x3 = rng.normal(0, 1, n)  # noise predictor
    epsilon = rng.normal(0, 0.5, n)
    y = 2.0 + beta1 * x1 + beta2 * x2 + 0.1 * x3 + epsilon

    gdf = gpd.GeoDataFrame(
        {
            "id": ids,
            "x1": x1,
            "x2": x2,
            "x3": x3,
            "y": y,
            "true_beta1": beta1,
            "true_beta2": beta2,
            "geometry": cells,
        },
        crs="EPSG:3857",
    )

    gpkg_path = output_dir / "demo_gwr.gpkg"
    gdf.to_file(gpkg_path, layer="dados", driver="GPKG")
    print(f"Demo data saved to {gpkg_path} ({n} observations).")


def main() -> None:
    parser = argparse.ArgumentParser(description="Cria dados demo para heterogeneidade_espacial.")
    parser.add_argument("--output-dir", default="data/demo", help="Diretório de saída.")
    parser.add_argument("--n", type=int, default=100, help="Número de observações.")
    parser.add_argument("--seed", type=int, default=20260007)
    args = parser.parse_args()
    create_demo(Path(args.output_dir), n=args.n, seed=args.seed)


if __name__ == "__main__":
    main()
