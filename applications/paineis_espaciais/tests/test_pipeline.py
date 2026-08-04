from __future__ import annotations

import json
from pathlib import Path

import pytest

from paineis_espaciais.pipeline import run_pipeline


def _write_config(tmp_path: Path, panel_csv: Path, weights_csv: Path) -> Path:
    out = tmp_path / "out"
    content = f"""
data:
  path: {panel_csv}
  unit_col: unit_id
  time_col: time_id

gap_strategy: none

models:
  - name: fe_baseline
    target: y
    predictors: [x1, x2]
    fixed_effects: unit
    model_type: fe

  - name: lag_espacial
    target: y
    predictors: [x1, x2]
    fixed_effects: unit
    model_type: spatial_lag

  - name: erro_espacial
    target: y
    predictors: [x1, x2]
    fixed_effects: unit
    model_type: spatial_error

weights:
  - name: queen
    path: {weights_csv}
    transformation: row_standardized

seed: 42
alpha: 0.05

output:
  dir: {out}
"""
    p = tmp_path / "config.yml"
    p.write_text(content, encoding="utf-8")
    return p


def test_pipeline_generates_expected_outputs(tmp_path, panel_csv_path, queen_weights_path):
    config_path = _write_config(tmp_path, panel_csv_path, queen_weights_path)
    products = run_pipeline(config_path)
    names = {p.name for p in products}

    required = {
        "diagnostico_painel.csv",
        "diagnostico_pesos.csv",
        "coeficientes.csv",
        "comparacao_modelos.csv",
        "notas_identificacao.csv",
        "relatorio.md",
        "manifesto.json",
    }
    assert required.issubset(names), f"Faltando: {required - names}"


def test_pipeline_manifest_has_seed(tmp_path, panel_csv_path, queen_weights_path):
    config_path = _write_config(tmp_path, panel_csv_path, queen_weights_path)
    products = run_pipeline(config_path)
    out = products[0].parent
    manifest = json.loads((out / "manifesto.json").read_text(encoding="utf-8"))
    assert manifest["seed"] == 42


def test_pipeline_coeficientes_not_empty(tmp_path, panel_csv_path, queen_weights_path):
    import pandas as pd

    config_path = _write_config(tmp_path, panel_csv_path, queen_weights_path)
    products = run_pipeline(config_path)
    out = products[0].parent
    coef = pd.read_csv(out / "coeficientes.csv")
    assert len(coef) > 0
    assert "model" in coef.columns
    assert "coef" in coef.columns


def test_pipeline_fe_only(tmp_path, panel_csv_path):
    """Pipeline funciona com apenas modelo FE (sem pesos)."""
    out = tmp_path / "out_fe"
    content = f"""
data:
  path: {panel_csv_path}
  unit_col: unit_id
  time_col: time_id
models:
  - name: fe_only
    target: y
    predictors: [x1]
    model_type: fe
output:
  dir: {out}
"""
    p = tmp_path / "config_fe.yml"
    p.write_text(content, encoding="utf-8")
    products = run_pipeline(p)
    names = {pp.name for pp in products}
    assert "coeficientes.csv" in names
    assert "manifesto.json" in names
