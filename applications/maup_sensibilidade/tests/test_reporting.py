from __future__ import annotations

import json
from pathlib import Path

import geopandas as gpd
import pytest

from maup_sensibilidade.aggregation import aggregate
from maup_sensibilidade.config import SchemeSpec
from maup_sensibilidade.reporting import write_manifest, write_report
from maup_sensibilidade.statistics import (
    MoranResult,
    descriptive_stats,
    stability_table,
)


def test_write_report_creates_file(tmp_path: Path, grid_gdf: gpd.GeoDataFrame) -> None:
    scheme = SchemeSpec(name="meso", dissolve_column="meso_id", weight_column=None)
    agg = aggregate(grid_gdf, scheme, ("renda",))
    desc = descriptive_stats({"meso": agg}, ("renda",))
    result = MoranResult(moran_i=0.3, expected=-0.25, p_value=0.02, permutations=99)
    stab = stability_table({"renda": {"meso": result}})
    report_path = tmp_path / "relatorio.md"
    write_report(
        report_path,
        desc,
        stab,
        {"renda": {"meso": True}},
        {"renda": {"meso": result}},
        0.05,
    )
    assert report_path.exists()
    content = report_path.read_text()
    assert "MAUP" in content
    assert "Moran" in content


def test_write_manifest(tmp_path: Path) -> None:
    manifest_path = tmp_path / "manifesto.json"
    dummy_input = tmp_path / "input.gpkg"
    dummy_input.write_bytes(b"dummy")
    write_manifest(
        manifest_path,
        config_path=tmp_path / "config.yml",
        inputs=[dummy_input],
        outputs=[tmp_path / "out.csv"],
        seed=42,
        permutations=99,
    )
    assert manifest_path.exists()
    data = json.loads(manifest_path.read_text())
    assert data["seed"] == 42
    assert data["permutations"] == 99
    assert str(dummy_input) in data["inputs"]
