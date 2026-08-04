from __future__ import annotations

import pytest
from heterogeneidade_espacial.config import ConfigError, load_config


def test_load_valid_config(demo_config):
    config_path, _ = demo_config
    cfg = load_config(config_path)
    assert cfg.target == "y"
    assert "x1" in cfg.predictors
    assert cfg.alpha == 0.05
    assert cfg.seed == 42


def test_missing_required_field(tmp_path):
    config = tmp_path / "bad.yml"
    config.write_text("data:\n  path: x.gpkg\n  id_column: id\n", encoding="utf-8")
    with pytest.raises(ConfigError):
        load_config(config)


def test_invalid_kernel(tmp_path, grid_gdf):
    _, gpkg = grid_gdf
    config = tmp_path / "cfg.yml"
    config.write_text(
        f"""
data:
  path: {gpkg}
  layer: dados
  id_column: id
model:
  target: y
  predictors: [x1]
bandwidth:
  kernel: invalid_kernel
run_mgwr: false
permutations: 99
seed: 1
alpha: 0.05
output:
  dir: {tmp_path / "out"}
""",
        encoding="utf-8",
    )
    with pytest.raises(ConfigError, match="Kernel"):
        load_config(config)


def test_permutations_minimum(tmp_path, grid_gdf):
    _, gpkg = grid_gdf
    config = tmp_path / "cfg.yml"
    config.write_text(
        f"""
data:
  path: {gpkg}
  layer: dados
  id_column: id
model:
  target: y
  predictors: [x1]
run_mgwr: false
permutations: 10
seed: 1
alpha: 0.05
output:
  dir: {tmp_path / "out"}
""",
        encoding="utf-8",
    )
    with pytest.raises(ConfigError, match="permutations"):
        load_config(config)
