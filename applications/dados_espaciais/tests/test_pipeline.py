import json
from pathlib import Path

import geopandas as gpd

from dados_espaciais.pipeline import run_pipeline


def test_pipeline_generates_all_products(pipeline_project: Path):
    outputs = run_pipeline(pipeline_project / "config" / "test.yml")
    assert set(outputs) == {"processed", "quality", "unmatched", "unused", "map", "manifest"}
    assert all(path.exists() for path in outputs.values())

    processed = gpd.read_file(outputs["processed"])
    assert len(processed) == 4
    assert processed.crs.to_string() == "EPSG:31983"
    assert processed["valor"].tolist() == [10, 20, 30, 40]

    quality = json.loads(outputs["quality"].read_text(encoding="utf-8"))
    assert quality["join"]["match_rate"] == 1.0
    assert quality["geometry"]["invalid_after"] == 0

    manifest = json.loads(outputs["manifest"].read_text(encoding="utf-8"))
    assert len(manifest["outputs"]) == 5
    assert all(len(item["sha256"]) == 64 for item in manifest["outputs"])
