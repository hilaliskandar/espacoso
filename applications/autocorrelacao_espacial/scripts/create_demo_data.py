from __future__ import annotations

from pathlib import Path

import geopandas as gpd
from shapely.geometry import box


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    output = root / "data" / "raw" / "territorios_demo.gpkg"
    output.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    cell = 1000.0
    x0, y0 = 330000.0, 7389000.0
    for row in range(4):
        for col in range(4):
            identifier = f"T{row + 1}{col + 1}"
            value = 100.0 - 12.0 * row - 9.0 * col
            rows.append(
                {
                    "id": identifier,
                    "indicador": value,
                    "geometry": box(x0 + col * cell, y0 + row * cell, x0 + (col + 1) * cell, y0 + (row + 1) * cell),
                }
            )
    rows.append(
        {
            "id": "ILHA",
            "indicador": 52.0,
            "geometry": box(x0 + 8000.0, y0 + 1000.0, x0 + 9000.0, y0 + 2000.0),
        }
    )
    gdf = gpd.GeoDataFrame(rows, crs="EPSG:31983")
    if output.exists():
        output.unlink()
    gdf.to_file(output, layer="territorios", driver="GPKG")
    print(output)


if __name__ == "__main__":
    main()
