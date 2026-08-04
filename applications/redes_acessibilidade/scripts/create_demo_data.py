"""
Cria fixture sintética de rede viária e unidades territoriais para demonstração.

A rede consiste em uma grade de 4 × 4 segmentos, com uma unidade isolada
(sem conexão na rede), permitindo diagnosticar componentes desconectados.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import geopandas as gpd
import pandas as pd
from shapely.geometry import LineString, box


def main() -> None:
    parser = argparse.ArgumentParser(description="Gera dados demo para redes_acessibilidade.")
    parser.add_argument(
        "--output",
        default=None,
        help="Diretório de saída (padrão: data/raw relativo ao script).",
    )
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    out_dir = Path(args.output) if args.output else root / "data" / "raw"
    out_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Rede viária sintética — grade 4 × 4 em EPSG:31983 (SIRGAS 2000 / UTM 23S)
    # Cada célula tem 1 km × 1 km
    # ------------------------------------------------------------------
    x0, y0 = 330_000.0, 7_389_000.0
    cell = 1_000.0
    cols = 4
    rows = 4

    edges = []
    # Segmentos horizontais
    for r in range(rows + 1):
        for c in range(cols):
            x_start = x0 + c * cell
            x_end = x0 + (c + 1) * cell
            y = y0 + r * cell
            edges.append({"edge_id": f"H{r}{c}", "geometry": LineString([(x_start, y), (x_end, y)])})

    # Segmentos verticais
    for r in range(rows):
        for c in range(cols + 1):
            x = x0 + c * cell
            y_start = y0 + r * cell
            y_end = y0 + (r + 1) * cell
            edges.append({"edge_id": f"V{r}{c}", "geometry": LineString([(x, y_start), (x, y_end)])})

    network_gdf = gpd.GeoDataFrame(edges, crs="EPSG:31983")

    # ------------------------------------------------------------------
    # Unidades territoriais (origens) — células da grade + 1 isolada
    # Cada unidade tem centróide snap-ável na rede
    # ------------------------------------------------------------------
    territories = []
    for r in range(rows):
        for c in range(cols):
            tid = f"T{r + 1}{c + 1}"
            geom = box(
                x0 + c * cell,
                y0 + r * cell,
                x0 + (c + 1) * cell,
                y0 + (r + 1) * cell,
            )
            # Oportunidades decrescem com distância ao centro
            opp = max(1, 100 - 10 * r - 8 * c)
            pop = 5_000 + 300 * r + 200 * c
            territories.append({"id": tid, "oportunidades": opp, "populacao": pop, "geometry": geom})

    # Unidade isolada — fora da grade, sem conexão na rede
    territories.append({
        "id": "ISOLADA",
        "oportunidades": 5,
        "populacao": 1_200,
        "geometry": box(x0 + 8_000, y0 + 1_000, x0 + 9_000, y0 + 2_000),
    })

    origins_gdf = gpd.GeoDataFrame(territories, crs="EPSG:31983")

    # ------------------------------------------------------------------
    # Exportação
    # ------------------------------------------------------------------
    net_path = out_dir / "rede_demo.gpkg"
    orig_path = out_dir / "territorios_demo.gpkg"

    if net_path.exists():
        net_path.unlink()
    if orig_path.exists():
        orig_path.unlink()

    network_gdf.to_file(net_path, layer="rede", driver="GPKG")
    origins_gdf.to_file(orig_path, layer="territorios", driver="GPKG")

    print(f"Rede:       {net_path}  ({len(network_gdf)} arestas)")
    print(f"Territórios: {orig_path}  ({len(origins_gdf)} unidades)")


if __name__ == "__main__":
    main()
