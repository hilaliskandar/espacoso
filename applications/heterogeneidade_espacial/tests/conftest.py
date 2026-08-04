from __future__ import annotations

import numpy as np
import geopandas as gpd
import pandas as pd
import pytest
from shapely.geometry import box


@pytest.fixture
def grid_gdf(tmp_path):
    """25-cell regular grid with spatially varying coefficients."""
    n = 25
    side = 5
    rng = np.random.default_rng(42)
    cells = []
    ids = []
    cx, cy = [], []
    for r in range(side):
        for c in range(side):
            cells.append(box(c, r, c + 1, r + 1))
            ids.append(f"C{r}{c}")
            cx.append(c + 0.5)
            cy.append(r + 0.5)

    cx = np.array(cx, dtype=float)
    cy = np.array(cy, dtype=float)
    x1 = rng.normal(0, 1, n)
    x2 = rng.normal(0, 1, n)
    beta1 = 1.0 + cx / cx.max()
    y = 2.0 + beta1 * x1 + 0.5 * x2 + rng.normal(0, 0.3, n)

    gdf = gpd.GeoDataFrame(
        {"id": ids, "x1": x1, "x2": x2, "y": y, "geometry": cells},
        crs="EPSG:3857",
    )
    gpkg = tmp_path / "grid.gpkg"
    gdf.to_file(gpkg, layer="dados", driver="GPKG")
    return gdf, gpkg


@pytest.fixture
def demo_config(tmp_path, grid_gdf):
    _, gpkg = grid_gdf
    output = tmp_path / "out"
    config = tmp_path / "config.yml"
    config.write_text(
        f"""
data:
  path: {gpkg}
  layer: dados
  id_column: id

model:
  target: y
  predictors: [x1, x2]
  add_constant: true
  robust_covariance: HC3

bandwidth:
  criterion: AICc
  kernel: bisquare
  fixed_or_adaptive: adaptive
  search_method: golden_section

run_mgwr: false

permutations: 99
seed: 42
alpha: 0.05
n_bootstrap: 0

output:
  dir: {output}
""",
        encoding="utf-8",
    )
    return config, output
