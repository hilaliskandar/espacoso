from __future__ import annotations

import hashlib
import json
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "naturalearth_lowres" / "naturalearth_lowres.shp"
OUT = ROOT / "data" / "processed" / "natural_earth_countries_v0_4.csv"
INDEX = ROOT / "data" / "processed" / "natural_earth_country_index_v0_4.csv"
PROVENANCE = ROOT / "data" / "processed" / "natural_earth_provenance_v0_4.json"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    gdf = gpd.read_file(RAW)
    gdf = gdf[~gdf["continent"].isin(["Antarctica", "Seven seas (open ocean)"])].copy()
    gdf = gdf[(gdf["pop_est"] > 0) & (gdf["gdp_md_est"] > 0)].copy()

    projected = gdf.to_crs("EPSG:6933")
    centroids = projected.geometry.centroid
    area_km2 = projected.geometry.area / 1_000_000.0
    perimeter_km = projected.geometry.length / 1_000.0
    compactness = 4.0 * np.pi * area_km2 / np.maximum(perimeter_km**2, 1e-12)

    data = pd.DataFrame(
        {
            "log_pop_est": np.log1p(gdf["pop_est"].to_numpy(dtype=float)),
            "log_area_km2": np.log1p(area_km2.to_numpy(dtype=float)),
            "log_perimeter_km": np.log1p(perimeter_km.to_numpy(dtype=float)),
            "compactness": compactness.to_numpy(dtype=float),
            "x_km": centroids.x.to_numpy(dtype=float) / 1_000.0,
            "y_km": centroids.y.to_numpy(dtype=float) / 1_000.0,
            "log_gdp_md_est": np.log1p(gdf["gdp_md_est"].to_numpy(dtype=float)),
        }
    )
    continent = pd.get_dummies(gdf["continent"], prefix="continent", dtype=float)
    data = pd.concat([data.reset_index(drop=True), continent.reset_index(drop=True)], axis=1)

    index = gdf[["name", "iso_a3", "continent", "pop_est", "gdp_md_est"]].reset_index(drop=True)
    index.insert(0, "row_id", np.arange(len(index), dtype=int))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    data.to_csv(OUT, index=False)
    index.to_csv(INDEX, index=False)

    raw_parts = sorted(RAW.parent.glob("naturalearth_lowres.*"))
    provenance = {
        "benchmark": "Natural Earth low-resolution countries",
        "source_scale": "1:110m",
        "source_fixture": "pyogrio/tests/fixtures/naturalearth_lowres",
        "upstream_url": "https://www.naturalearthdata.com/downloads/110m-cultural-vectors/",
        "source_files_sha256": {p.name: sha256(p) for p in raw_parts},
        "processed_csv_sha256": sha256(OUT),
        "country_index_sha256": sha256(INDEX),
        "crs_source": str(gdf.crs),
        "crs_analysis": "EPSG:6933",
        "excluded_continents": ["Antarctica", "Seven seas (open ocean)"],
        "n_observations": int(len(data)),
        "target": "log1p(gdp_md_est)",
        "features": [c for c in data.columns if c not in {"x_km", "y_km", "log_gdp_md_est"}],
        "coordinate_columns": ["x_km", "y_km"],
    }
    PROVENANCE.write_text(json.dumps(provenance, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(provenance, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
