"""Gera a fixture sintética mínima para testes e demonstração.

A malha é uma grade 4×4 com um unidade isolada. Ela não representa
território real e pode ser distribuída com o repositório.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import geopandas as gpd
from shapely.geometry import box


def create_demo_grid(output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    indicadores = [
        3.2, 4.1, 2.8, 5.0,
        1.5, 3.9, 4.7, 2.2,
        5.5, 1.1, 3.3, 4.4,
        2.9, 3.6, 4.8, 1.8,
    ]
    idx = 0
    for row in range(4):
        for col in range(4):
            rows.append(
                {
                    "id": f"t{row:02d}{col:02d}",
                    "indicador": indicadores[idx],
                    "covar1": float(row + 1),
                    "covar2": float(col + 1),
                    "geometry": box(
                        col * 10_000,
                        row * 10_000,
                        col * 10_000 + 10_000,
                        row * 10_000 + 10_000,
                    ),
                }
            )
            idx += 1
    # unidade isolada
    rows.append(
        {
            "id": "t_island",
            "indicador": 3.0,
            "covar1": 0.0,
            "covar2": 0.0,
            "geometry": box(200_000, 0, 210_000, 10_000),
        }
    )
    gdf = gpd.GeoDataFrame(rows, crs="EPSG:31983")
    out = output_dir / "territorios_demo.gpkg"
    gdf.to_file(out, layer="territorios", driver="GPKG")
    print(f"[demo] {len(gdf)} unidades → {out}")
    return out


def main():
    parser = argparse.ArgumentParser(description="Cria fixture sintética")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/raw"),
        help="Diretório de saída (padrão: data/raw)",
    )
    args = parser.parse_args()
    create_demo_grid(args.output_dir)


if __name__ == "__main__":
    main()
