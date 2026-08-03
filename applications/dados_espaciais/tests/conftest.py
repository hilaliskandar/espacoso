from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import pandas as pd
import pytest
from shapely.geometry import Polygon, box


@pytest.fixture
def valid_spatial() -> gpd.GeoDataFrame:
    return gpd.GeoDataFrame(
        {
            "id": ["A", "B", "C"],
            "geometry": [
                box(-46.7, -23.6, -46.69, -23.59),
                box(-46.69, -23.6, -46.68, -23.59),
                box(-46.68, -23.6, -46.67, -23.59),
            ],
        },
        crs="EPSG:4326",
    )


@pytest.fixture
def valid_table() -> pd.DataFrame:
    return pd.DataFrame({"codigo": ["A", "B", "C"], "valor": [1.0, 2.0, 3.0]})


@pytest.fixture
def bowtie_spatial() -> gpd.GeoDataFrame:
    invalid = Polygon([(0, 0), (1, 1), (1, 0), (0, 1), (0, 0)])
    return gpd.GeoDataFrame({"id": ["X"], "geometry": [invalid]}, crs="EPSG:4326")


@pytest.fixture
def pipeline_project(tmp_path: Path) -> Path:
    root = tmp_path / "project"
    (root / "config").mkdir(parents=True)
    (root / "data" / "raw").mkdir(parents=True)
    spatial = gpd.GeoDataFrame(
        {
            "id": ["A", "B", "C", "D"],
            "geometry": [
                box(-46.72, -23.64, -46.71, -23.63),
                box(-46.71, -23.64, -46.70, -23.63),
                box(-46.72, -23.63, -46.71, -23.62),
                box(-46.71, -23.63, -46.70, -23.62),
            ],
        },
        crs="EPSG:4326",
    )
    table = pd.DataFrame(
        {"codigo": ["A", "B", "C", "D"], "valor": [10, 20, 30, 40]}
    )
    spatial.to_file(root / "data" / "raw" / "spatial.gpkg", driver="GPKG")
    table.to_csv(root / "data" / "raw" / "table.csv", index=False)
    (root / "config" / "test.yml").write_text(
        """
paths:
  spatial: ../data/raw/spatial.gpkg
  table: ../data/raw/table.csv
  output_dir: ../outputs/test
keys:
  spatial: id
  table: codigo
crs:
  analysis: EPSG:31983
geometry:
  repair_invalid: true
  allow_empty: false
join:
  minimum_match_rate: 1.0
table:
  numeric_columns: [valor]
map:
  column: valor
  output: mapa.png
  title: Teste
  scheme: quantiles
  k: 3
""".strip(),
        encoding="utf-8",
    )
    return root
