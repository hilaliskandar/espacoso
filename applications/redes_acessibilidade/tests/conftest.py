"""Fixtures compartilhadas para os testes de redes e acessibilidade."""
from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import pandas as pd
import pytest
from shapely.geometry import LineString, box


@pytest.fixture
def simple_network() -> gpd.GeoDataFrame:
    """Rede simples de 4 arestas formando um quadrado 2×2 km."""
    edges = [
        {"edge_id": "H0", "geometry": LineString([(0, 0), (1000, 0)])},
        {"edge_id": "H1", "geometry": LineString([(1000, 0), (2000, 0)])},
        {"edge_id": "V0", "geometry": LineString([(0, 0), (0, 1000)])},
        {"edge_id": "V1", "geometry": LineString([(0, 1000), (0, 2000)])},
        {"edge_id": "D0", "geometry": LineString([(1000, 0), (1000, 1000)])},
        {"edge_id": "D1", "geometry": LineString([(0, 1000), (1000, 1000)])},
    ]
    gdf = gpd.GeoDataFrame(edges, crs="EPSG:31983")
    gdf["length_m"] = gdf.geometry.length
    return gdf


@pytest.fixture
def simple_origins() -> gpd.GeoDataFrame:
    """Três unidades territoriais conectadas à rede simples."""
    rows = [
        {"id": "A", "oportunidades": 100, "populacao": 5000,
         "geometry": box(0, 0, 500, 500)},
        {"id": "B", "oportunidades": 50, "populacao": 3000,
         "geometry": box(1000, 0, 1500, 500)},
        {"id": "C", "oportunidades": 30, "populacao": 2000,
         "geometry": box(0, 1000, 500, 1500)},
    ]
    return gpd.GeoDataFrame(rows, crs="EPSG:31983")


@pytest.fixture
def pipeline_project(tmp_path: Path) -> Path:
    """Projeto completo mínimo para testar o pipeline."""
    root = tmp_path / "project"
    (root / "config").mkdir(parents=True)
    (root / "data" / "raw").mkdir(parents=True)

    # Rede: grade 3×3 segmentos
    x0, y0 = 330_000.0, 7_389_000.0
    cell = 1_000.0
    edges = []
    for r in range(4):
        for c in range(3):
            edges.append({
                "edge_id": f"H{r}{c}",
                "geometry": LineString([
                    (x0 + c * cell, y0 + r * cell),
                    (x0 + (c + 1) * cell, y0 + r * cell),
                ]),
            })
    for r in range(3):
        for c in range(4):
            edges.append({
                "edge_id": f"V{r}{c}",
                "geometry": LineString([
                    (x0 + c * cell, y0 + r * cell),
                    (x0 + c * cell, y0 + (r + 1) * cell),
                ]),
            })
    net = gpd.GeoDataFrame(edges, crs="EPSG:31983")
    net.to_file(root / "data" / "raw" / "rede.gpkg", layer="rede", driver="GPKG")

    # Origens: 4 territórios
    territories = []
    for r in range(2):
        for c in range(2):
            territories.append({
                "id": f"T{r}{c}",
                "oportunidades": 100 - r * 20 - c * 15,
                "populacao": 5000 + r * 500,
                "geometry": box(
                    x0 + c * cell, y0 + r * cell,
                    x0 + (c + 1) * cell, y0 + (r + 1) * cell,
                ),
            })
    orig = gpd.GeoDataFrame(territories, crs="EPSG:31983")
    orig.to_file(root / "data" / "raw" / "territorios.gpkg", layer="territorios", driver="GPKG")

    (root / "config" / "test.yml").write_text(
        """
data:
  network_path: ../data/raw/rede.gpkg
  network_layer: rede
  origins_path: ../data/raw/territorios.gpkg
  origins_layer: territorios
  origins_id_column: id
  opportunities_column: oportunidades
  population_column: populacao
  analysis_crs: EPSG:31983

analysis:
  impedances:
    - name: linear_5km
      function: linear
      cutoff: 5000.0
    - name: exp_neg
      function: negative_exponential
      beta: 0.001
  centrality:
    - degree
  max_cost: 20000.0
  seed: 42

output:
  directory: ../outputs/test
  maps: false
""".strip(),
        encoding="utf-8",
    )
    return root
