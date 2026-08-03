from __future__ import annotations

import argparse
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.geometry import box


def _edges(rows: int, cols: int, queen: bool) -> pd.DataFrame:
    offsets = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    if queen:
        offsets += [(-1, -1), (-1, 1), (1, -1), (1, 1)]
    result: list[dict[str, str | float]] = []
    for row in range(rows):
        for col in range(cols):
            origin = f"U{row:02d}{col:02d}"
            for dr, dc in offsets:
                rr, cc = row + dr, col + dc
                if 0 <= rr < rows and 0 <= cc < cols:
                    result.append(
                        {
                            "origin_id": origin,
                            "destination_id": f"U{rr:02d}{cc:02d}",
                            "weight": 1.0,
                        }
                    )
    return pd.DataFrame(result)


def create_demo(output_dir: Path, rows: int = 8, cols: int = 8, seed: int = 20260001) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(seed)
    records = []
    for row in range(rows):
        for col in range(cols):
            x1 = (col - (cols - 1) / 2) / ((cols - 1) / 2)
            x2 = np.sin((row + 1) * np.pi / (rows + 1)) + 0.15 * np.cos(col)
            z_spatial = np.exp(-(((row - 1.5) / 2.2) ** 2 + ((col - 1.5) / 2.2) ** 2))
            scale = 0.06 + 0.18 * (x1 + 1.05) ** 2
            noise = rng.normal(0.0, scale)
            y = 5.0 + 2.0 * x1 - 1.5 * x2 + 4.0 * z_spatial + noise
            records.append(
                {
                    "id": f"U{row:02d}{col:02d}",
                    "x1": x1,
                    "x2": x2,
                    "z_spatial": z_spatial,
                    "y": y,
                    "geometry": box(col * 1000, row * 1000, (col + 1) * 1000, (row + 1) * 1000),
                }
            )
    gdf = gpd.GeoDataFrame(records, crs="EPSG:3857")
    data_path = output_dir / "demo_ols.gpkg"
    if data_path.exists():
        data_path.unlink()
    gdf.to_file(data_path, layer="dados", driver="GPKG")
    _edges(rows, cols, queen=False).to_csv(output_dir / "pesos_rook.csv", index=False)
    _edges(rows, cols, queen=True).to_csv(output_dir / "pesos_queen.csv", index=False)
    print(data_path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="data/demo")
    args = parser.parse_args()
    create_demo(Path(args.output_dir))


if __name__ == "__main__":
    main()
