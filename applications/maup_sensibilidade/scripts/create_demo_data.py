from __future__ import annotations

"""Gera dados sintéticos para a demonstração do MAUP.

Cria uma grade regular de unidades de base (micro) com valores simulados e
dois esquemas de agregação superiores (meso e macro) codificados via colunas
de dissolução.
"""

import argparse
from pathlib import Path

import geopandas as gpd
import numpy as np
from shapely.geometry import box


def create_demo(output_dir: Path, rows: int = 12, cols: int = 12, seed: int = 20260006) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(seed)

    records = []
    for r in range(rows):
        for c in range(cols):
            # Fator espacial suave (gradiente Norte-Sul + ruído)
            spatial_factor = np.sin((r + 1) * np.pi / (rows + 1))
            noise = rng.normal(0.0, 0.1)
            renda = 3000 + 2000 * spatial_factor + 500 * (c / cols) + rng.normal(0.0, 200)
            populacao = max(100.0, 1000 + 800 * spatial_factor + rng.normal(0.0, 150))

            # Esquema meso: blocos 3×3
            meso_row = r // 3
            meso_col = c // 3
            meso_id = f"M{meso_row:02d}{meso_col:02d}"

            # Esquema macro: blocos 6×6
            macro_row = r // 6
            macro_col = c // 6
            macro_id = f"A{macro_row:02d}{macro_col:02d}"

            records.append(
                {
                    "id": f"U{r:02d}{c:02d}",
                    "row": r,
                    "col": c,
                    "renda_media": round(renda, 2),
                    "populacao": round(populacao, 1),
                    "meso_id": meso_id,
                    "macro_id": macro_id,
                    "geometry": box(c * 1000, r * 1000, (c + 1) * 1000, (r + 1) * 1000),
                }
            )

    gdf = gpd.GeoDataFrame(records, crs="EPSG:3857")
    data_path = output_dir / "demo_maup.gpkg"
    if data_path.exists():
        data_path.unlink()
    gdf.to_file(data_path, layer="micro", driver="GPKG")
    print(data_path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Criar dados de demonstração MAUP")
    parser.add_argument("--output-dir", default="data/demo")
    args = parser.parse_args()
    create_demo(Path(args.output_dir))


if __name__ == "__main__":
    main()
