from __future__ import annotations

import pytest
from pathlib import Path

from paineis_espaciais.config import load_config
from paineis_espaciais.errors import PanelError


def _write_config(tmp_path: Path, content: str) -> Path:
    p = tmp_path / "config.yml"
    p.write_text(content, encoding="utf-8")
    return p


def _minimal_config(tmp_path: Path, panel_csv: Path, weights_csv: Path) -> str:
    return f"""
data:
  path: {panel_csv}
  unit_col: unit_id
  time_col: time_id
models:
  - name: fe_test
    target: y
    predictors: [x1, x2]
    model_type: fe
weights:
  - name: queen
    path: {weights_csv}
output:
  dir: {tmp_path / "out"}
"""


def test_load_config_minimal(tmp_path, panel_csv_path, queen_weights_path):
    cfg_text = _minimal_config(tmp_path, panel_csv_path, queen_weights_path)
    p = _write_config(tmp_path, cfg_text)
    config = load_config(p)
    assert config.unit_col == "unit_id"
    assert config.time_col == "time_id"
    assert len(config.models) == 1
    assert len(config.weights) == 1


def test_load_config_defaults(tmp_path, panel_csv_path, queen_weights_path):
    cfg_text = _minimal_config(tmp_path, panel_csv_path, queen_weights_path)
    p = _write_config(tmp_path, cfg_text)
    config = load_config(p)
    assert config.gap_strategy == "none"
    assert config.alpha == 0.05
    assert config.seed == 42


def test_load_config_missing_data_raises(tmp_path, queen_weights_path):
    content = f"""
models:
  - name: fe
    target: y
    predictors: [x1]
weights:
  - name: q
    path: {queen_weights_path}
output:
  dir: {tmp_path / "out"}
"""
    p = _write_config(tmp_path, content)
    with pytest.raises(PanelError, match="data"):
        load_config(p)


def test_load_config_invalid_fe_raises(tmp_path, panel_csv_path, queen_weights_path):
    content = f"""
data:
  path: {panel_csv_path}
  unit_col: unit_id
  time_col: time_id
models:
  - name: m
    target: y
    predictors: [x1]
    fixed_effects: bad_fe
output:
  dir: {tmp_path / "out"}
"""
    p = _write_config(tmp_path, content)
    with pytest.raises(PanelError, match="fixed_effects"):
        load_config(p)


def test_load_config_spatial_without_weights_raises(tmp_path, panel_csv_path):
    content = f"""
data:
  path: {panel_csv_path}
  unit_col: unit_id
  time_col: time_id
models:
  - name: sl
    target: y
    predictors: [x1]
    model_type: spatial_lag
output:
  dir: {tmp_path / "out"}
"""
    p = _write_config(tmp_path, content)
    with pytest.raises(PanelError, match="pesos"):
        load_config(p)


def test_load_config_invalid_alpha_raises(tmp_path, panel_csv_path, queen_weights_path):
    content = f"""
data:
  path: {panel_csv_path}
  unit_col: unit_id
  time_col: time_id
models:
  - name: m
    target: y
    predictors: [x1]
weights:
  - name: q
    path: {queen_weights_path}
alpha: 1.5
output:
  dir: {tmp_path / "out"}
"""
    p = _write_config(tmp_path, content)
    with pytest.raises(PanelError, match="alpha"):
        load_config(p)
