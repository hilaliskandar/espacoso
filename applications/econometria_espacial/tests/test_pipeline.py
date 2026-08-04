"""Testes de integração do pipeline completo."""
from __future__ import annotations

from pathlib import Path

import pytest

from econometria_espacial.pipeline import run_pipeline


def _write_config(tmp_path: Path, data_path: Path, weights_path: Path) -> Path:
    content = f"""
data:
  path: {data_path}
  layer: dados
  id_column: id

weights:
  - name: rook
    path: {weights_path}
    transformation: row_standardized

models:
  - name: OLS
    model_type: OLS
    target: y
    predictors: [x1, x2]
    weights_name: rook

  - name: SAR
    model_type: SAR
    target: y
    predictors: [x1, x2]
    weights_name: rook

  - name: SEM
    model_type: SEM
    target: y
    predictors: [x1, x2]
    weights_name: rook

  - name: SLX
    model_type: SLX
    target: y
    predictors: [x1, x2]
    weights_name: rook

  - name: SDM
    model_type: SDM
    target: y
    predictors: [x1, x2]
    weights_name: rook

primary_model: SAR
primary_weights: rook
permutations: 99
seed: 42
alpha: 0.05

output:
  dir: {tmp_path / "out"}
"""
    p = tmp_path / "config.yml"
    p.write_text(content, encoding="utf-8")
    return p


def test_pipeline_produces_outputs(tmp_path, grid_4x1):
    _, gpkg, weights = grid_4x1
    cfg = _write_config(tmp_path, gpkg, weights)
    outputs = run_pipeline(cfg)
    assert len(outputs) > 0
    paths = {Path(p).name for p in outputs}
    assert "coeficientes.csv" in paths
    assert "impactos.csv" in paths
    assert "relatorio.md" in paths
    assert "manifesto.json" in paths


def test_pipeline_coeficientes_has_all_models(tmp_path, grid_4x1):
    _, gpkg, weights = grid_4x1
    cfg = _write_config(tmp_path, gpkg, weights)
    run_pipeline(cfg)
    import pandas as pd
    coef = pd.read_csv(tmp_path / "out" / "coeficientes.csv")
    model_names = set(coef["model"])
    assert {"OLS", "SAR", "SEM", "SLX", "SDM"} == model_names


def test_pipeline_impacts_verification(tmp_path, grid_4x1):
    """Verificação numérica: direto + indireto ≈ total para todos os modelos."""
    _, gpkg, weights = grid_4x1
    cfg = _write_config(tmp_path, gpkg, weights)
    run_pipeline(cfg)
    import pandas as pd
    check = pd.read_csv(tmp_path / "out" / "verificacao_impactos.csv")
    assert check["ok"].all(), f"Impactos não verificados:\n{check[~check['ok']]}"


def test_pipeline_report_exists(tmp_path, grid_4x1):
    _, gpkg, weights = grid_4x1
    cfg = _write_config(tmp_path, gpkg, weights)
    run_pipeline(cfg)
    report = tmp_path / "out" / "relatorio.md"
    assert report.exists()
    content = report.read_text(encoding="utf-8")
    assert "Decomposição de Impactos" in content
    assert "coeficientes autorregressivos" in content
