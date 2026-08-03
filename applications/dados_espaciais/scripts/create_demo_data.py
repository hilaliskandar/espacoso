from __future__ import annotations

import argparse
from pathlib import Path

import geopandas as gpd
import pandas as pd
from shapely.geometry import box


def create_demo(output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    indicators = []
    start_lon, start_lat = -46.72, -23.64
    step = 0.02
    value = 10
    for row in range(3):
        for col in range(3):
            identifier = f"T{row + 1}{col + 1}"
            minx = start_lon + col * step
            miny = start_lat + row * step
            rows.append(
                {
                    "id_territorio": identifier,
                    "nome": f"Território {row + 1}-{col + 1}",
                    "geometry": box(minx, miny, minx + step, miny + step),
                }
            )
            indicators.append(
                {
                    "id_territorio": identifier,
                    "indicador": value + row * 8 + col * 3,
                    "populacao": 1000 + row * 500 + col * 250,
                }
            )
    spatial = gpd.GeoDataFrame(rows, crs="EPSG:4326")
    table = pd.DataFrame(indicators)
    spatial_path = output_dir / "territorios_demo.gpkg"
    table_path = output_dir / "indicadores_demo.csv"
    spatial.to_file(spatial_path, driver="GPKG")
    table.to_csv(table_path, index=False)
    return spatial_path, table_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Gera a base demonstrativa da A1.")
    parser.add_argument("--output", default="data/raw")
    args = parser.parse_args()
    spatial, table = create_demo(Path(args.output))
    print(spatial)
    print(table)


if __name__ == "__main__":
    main()
