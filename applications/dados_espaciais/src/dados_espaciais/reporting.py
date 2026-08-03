from __future__ import annotations

import hashlib
import json
import platform
from datetime import datetime, timezone
from pathlib import Path

import geopandas as gpd


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def spatial_metrics(frame: gpd.GeoDataFrame) -> dict:
    areas = frame.geometry.area
    bounds = [float(value) for value in frame.total_bounds]
    return {
        "n_features": int(len(frame)),
        "bbox": bounds,
        "area_min": float(areas.min()),
        "area_median": float(areas.median()),
        "area_max": float(areas.max()),
        "geometry_types": frame.geometry.geom_type.value_counts().to_dict(),
    }


def write_json(data: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def make_manifest(
    config_path: Path,
    spatial_path: Path,
    table_path: Path,
    output_files: list[Path],
) -> dict:
    try:
        import geopandas
        import matplotlib
        import pandas
        import shapely
    except ImportError:  # pragma: no cover
        geopandas = matplotlib = pandas = shapely = None
    return {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "versions": {
            "geopandas": getattr(geopandas, "__version__", None),
            "pandas": getattr(pandas, "__version__", None),
            "shapely": getattr(shapely, "__version__", None),
            "matplotlib": getattr(matplotlib, "__version__", None),
        },
        "inputs": {
            "config": {"path": str(config_path), "sha256": sha256(config_path)},
            "spatial": {"path": str(spatial_path), "sha256": sha256(spatial_path)},
            "table": {"path": str(table_path), "sha256": sha256(table_path)},
        },
        "outputs": [
            {"path": str(path), "sha256": sha256(path)}
            for path in output_files
            if path.exists() and path.is_file()
        ],
    }
