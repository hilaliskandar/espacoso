from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import pandas as pd
import pytest
from shapely.geometry import box


@pytest.fixture
def four_grid(tmp_path: Path):
    gdf = gpd.GeoDataFrame(
        {
            "id": ["A", "B", "C", "D"],
            "x1": [0.0, 1.0, 2.0, 3.0],
            "x2": [1.0, 0.0, 1.0, 0.0],
            "y": [1.0, 3.1, 4.9, 7.2],
            "geometry": [box(0, 0, 1, 1), box(1, 0, 2, 1), box(2, 0, 3, 1), box(3, 0, 4, 1)],
        },
        crs="EPSG:3857",
    )
    gpkg = tmp_path / "data.gpkg"
    gdf.to_file(gpkg, layer="dados", driver="GPKG")
    edges = pd.DataFrame(
        {
            "origin_id": ["A", "B", "B", "C", "C", "D"],
            "destination_id": ["B", "A", "C", "B", "D", "C"],
            "weight": [1.0] * 6,
        }
    )
    weights = tmp_path / "weights.csv"
    edges.to_csv(weights, index=False)
    return gdf, gpkg, weights
