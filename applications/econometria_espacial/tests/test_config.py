"""Testes de carregamento e validação de configuração."""
from __future__ import annotations

from pathlib import Path

import pytest

from econometria_espacial.config import load_config
from econometria_espacial.errors import ConfigError


def _write_config(tmp_path: Path, content: str) -> Path:
    p = tmp_path / "config.yml"
    p.write_text(content, encoding="utf-8")
    return p


def _minimal_config(tmp_path: Path, data_path: Path, weights_path: Path) -> str:
    return f"""
data:
  path: {data_path}
  layer: dados
  id_column: id

weights:
  - name: rook
    path: {weights_path}
    transformation: row_standardized

models:
  - name: SAR
    model_type: SAR
    target: y
    predictors: [x1]
    weights_name: rook

primary_model: SAR
primary_weights: rook
permutations: 99
seed: 42
alpha: 0.05

output:
  dir: {tmp_path / "out"}
"""


def test_load_config_valid(tmp_path, grid_4x1):
    _, gpkg, weights = grid_4x1
    cfg_text = _minimal_config(tmp_path, gpkg, weights)
    p = _write_config(tmp_path, cfg_text)
    cfg = load_config(p)
    assert cfg.models[0].model_type == "SAR"
    assert cfg.primary_model == "SAR"
    assert cfg.primary_weights == "rook"


def test_load_config_missing_required(tmp_path):
    p = _write_config(tmp_path, "models: []\n")
    with pytest.raises(ConfigError):
        load_config(p)


def test_load_config_invalid_transformation(tmp_path, grid_4x1):
    _, gpkg, weights = grid_4x1
    content = f"""
data:
  path: {gpkg}
  id_column: id
weights:
  - name: bad
    path: {weights}
    transformation: kd_tree
models:
  - name: OLS
    model_type: OLS
    target: y
    predictors: [x1]
    weights_name: bad
primary_model: OLS
primary_weights: bad
permutations: 99
alpha: 0.05
output:
  dir: {tmp_path}/out
"""
    p = _write_config(tmp_path, content)
    with pytest.raises(ConfigError, match="Transformação"):
        load_config(p)


def test_load_config_invalid_model_type(tmp_path, grid_4x1):
    _, gpkg, weights = grid_4x1
    content = f"""
data:
  path: {gpkg}
  id_column: id
weights:
  - name: rook
    path: {weights}
models:
  - name: X
    model_type: NOPE
    target: y
    predictors: [x1]
    weights_name: rook
primary_model: X
primary_weights: rook
permutations: 99
alpha: 0.05
output:
  dir: {tmp_path}/out
"""
    p = _write_config(tmp_path, content)
    with pytest.raises(ConfigError, match="modelo não suportado"):
        load_config(p)
