from __future__ import annotations

import geopandas as gpd
import numpy as np
import pytest
from shapely.geometry import box


@pytest.fixture
def grid_gdf() -> gpd.GeoDataFrame:
    """Grade 4×4 com duas variáveis e colunas de dissolução."""
    rows_list = []
    for r in range(4):
        for c in range(4):
            spatial = np.sin((r + 1) * np.pi / 5)
            rows_list.append(
                {
                    "id": f"U{r:02d}{c:02d}",
                    "renda": 1000.0 + 500.0 * spatial + float(c * 100),
                    "populacao": 200.0 + float(r * 50),
                    "meso_id": f"M{r // 2}{c // 2}",
                    "geometry": box(c * 1000, r * 1000, (c + 1) * 1000, (r + 1) * 1000),
                }
            )
    return gpd.GeoDataFrame(rows_list, crs="EPSG:3857")
