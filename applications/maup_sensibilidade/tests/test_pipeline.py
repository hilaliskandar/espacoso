from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import numpy as np
import pytest
from shapely.geometry import box

from maup_sensibilidade.config import AnalysisConfig, SchemeSpec
from maup_sensibilidade.pipeline import run_pipeline


def _build_config(tmp_path: Path) -> tuple[Path, Path]:
    """Cria dados demo e config mínima para o teste de pipeline."""
    from shapely.geometry import box
    import geopandas as gpd
    import numpy as np

    rng = np.random.default_rng(0)
    records = []
    for r in range(6):
        for c in range(6):
            records.append(
                {
                    "id": f"U{r}{c}",
                    "renda": 1000.0 + rng.normal(0, 100),
                    "populacao": 200.0 + rng.normal(0, 20),
                    "meso_id": f"M{r // 2}{c // 2}",
                    "geometry": box(c * 1000, r * 1000, (c + 1) * 1000, (r + 1) * 1000),
                }
            )
    gdf = gpd.GeoDataFrame(records, crs="EPSG:3857")
    data_path = tmp_path / "demo_maup.gpkg"
    gdf.to_file(data_path, layer="micro", driver="GPKG")

    output_dir = tmp_path / "outputs"
    cfg_content = f"""
data:
  path: {data_path}
  layer: micro
  id_column: id
variables:
  - renda
  - populacao
schemes:
  - name: micro
    dissolve_column: null
  - name: meso
    dissolve_column: meso_id
permutations: 99
seed: 42
alpha: 0.05
output:
  dir: {output_dir}
"""
    cfg_path = tmp_path / "config.yml"
    cfg_path.write_text(cfg_content, encoding="utf-8")
    return cfg_path, output_dir


def test_pipeline_produces_outputs(tmp_path: Path) -> None:
    cfg_path, output_dir = _build_config(tmp_path)
    outputs = run_pipeline(cfg_path)
    assert len(outputs) > 0
    for p in outputs:
        assert Path(p).exists(), f"Arquivo de saída ausente: {p}"


def test_pipeline_creates_report(tmp_path: Path) -> None:
    cfg_path, output_dir = _build_config(tmp_path)
    run_pipeline(cfg_path)
    report = output_dir / "relatorio.md"
    assert report.exists()
    assert "MAUP" in report.read_text()


def test_pipeline_creates_manifest(tmp_path: Path) -> None:
    cfg_path, output_dir = _build_config(tmp_path)
    run_pipeline(cfg_path)
    manifest = output_dir / "manifesto.json"
    assert manifest.exists()


def test_pipeline_creates_stability_csv(tmp_path: Path) -> None:
    cfg_path, output_dir = _build_config(tmp_path)
    run_pipeline(cfg_path)
    stab = output_dir / "estabilidade_moran.csv"
    assert stab.exists()


def test_pipeline_creates_conservation_csv(tmp_path: Path) -> None:
    cfg_path, output_dir = _build_config(tmp_path)
    run_pipeline(cfg_path)
    conserv = output_dir / "conservacao_totais.csv"
    assert conserv.exists()
