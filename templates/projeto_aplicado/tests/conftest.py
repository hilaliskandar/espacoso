"""Fixtures compartilhadas para os testes do projeto aplicado."""

from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import pytest
from shapely.geometry import box


@pytest.fixture
def demo_gdf() -> gpd.GeoDataFrame:
    """Grade sintética 3×3 com uma unidade isolada."""
    rows = []
    for row in range(3):
        for col in range(3):
            rows.append(
                {
                    "id": f"{row}{col}",
                    "indicador": float(row * 3 + col + 1),
                    "geometry": box(col, row, col + 1, row + 1),
                }
            )
    # unidade isolada
    rows.append({"id": "island", "indicador": 5.0, "geometry": box(10, 0, 11, 1)})
    return gpd.GeoDataFrame(rows, crs="EPSG:3857")


@pytest.fixture
def demo_config(tmp_path: Path) -> dict:
    """Configuração mínima válida para os testes."""
    gpkg = tmp_path / "base.gpkg"
    gdf = gpd.GeoDataFrame(
        [{"id": "a", "indicador": 1.0, "geometry": box(0, 0, 1, 1)}],
        crs="EPSG:3857",
    )
    gdf.to_file(gpkg, layer="territorios", driver="GPKG")

    return {
        "projeto": {
            "titulo": "Projeto de Teste",
            "participante": "Participante Teste",
            "orientador": "Orientador Teste",
            "versao": "0.1.0",
            "data_execucao": "2026-08-04",
        },
        "data": {
            "path": str(gpkg),
            "layer": "territorios",
            "id_column": "id",
            "value_column": "indicador",
            "analysis_crs": "EPSG:3857",
        },
        "reproducao": {
            "seed": 42,
            "permutations": 99,
        },
        "saida": {
            "directory": str(tmp_path / "outputs"),
            "relatorio": True,
            "manifesto": True,
            "geopackage": False,
            "mapas": False,
        },
    }
