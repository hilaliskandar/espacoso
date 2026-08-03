from __future__ import annotations

import geopandas as gpd
import pytest
from shapely.geometry import box


@pytest.fixture
def grid_gdf() -> gpd.GeoDataFrame:
    rows = []
    for row in range(2):
        for col in range(2):
            rows.append(
                {
                    "id": f"{row}{col}",
                    "value": float(row * 2 + col + 1),
                    "geometry": box(col, row, col + 1, row + 1),
                }
            )
    rows.append({"id": "island", "value": 3.0, "geometry": box(10, 0, 11, 1)})
    return gpd.GeoDataFrame(rows, crs="EPSG:3857")
