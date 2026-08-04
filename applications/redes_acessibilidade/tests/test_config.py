"""Testes de configuração."""
from __future__ import annotations

from pathlib import Path

import pytest

from redes_acessibilidade.config import load_config, AppConfig
from redes_acessibilidade.errors import ConfigError


def _write_config(tmp_path: Path, content: str) -> Path:
    p = tmp_path / "cfg.yml"
    p.write_text(content, encoding="utf-8")
    return p


_VALID = """
data:
  network_path: rede.gpkg
  origins_path: origens.gpkg
  origins_id_column: id
  opportunities_column: opp
  population_column: pop
  analysis_crs: EPSG:31983

analysis:
  impedances:
    - name: lin
      function: linear
      cutoff: 5000.0
    - name: exp
      function: negative_exponential
      beta: 0.001
  max_cost: 10000.0

output:
  directory: outputs
"""


def test_load_valid_config(tmp_path: Path):
    cfg = load_config(_write_config(tmp_path, _VALID))
    assert isinstance(cfg, AppConfig)
    assert len(cfg.impedances) == 2
    assert cfg.impedances[0].name == "lin"
    assert cfg.impedances[1].function == "negative_exponential"
    assert cfg.max_cost == 10000.0


def test_missing_network_path(tmp_path: Path):
    content = """
data:
  origins_path: origens.gpkg
  origins_id_column: id
  opportunities_column: opp
  population_column: pop
  analysis_crs: EPSG:31983
analysis:
  impedances:
    - name: lin
      function: linear
      cutoff: 5000.0
    - name: exp
      function: negative_exponential
      beta: 0.001
  max_cost: 10000.0
output:
  directory: outputs
"""
    with pytest.raises(ConfigError, match="network_path"):
        load_config(_write_config(tmp_path, content))


def test_missing_origins_path(tmp_path: Path):
    content = """
data:
  network_path: rede.gpkg
  origins_id_column: id
  opportunities_column: opp
  population_column: pop
  analysis_crs: EPSG:31983
analysis:
  impedances:
    - name: lin
      function: linear
      cutoff: 5000.0
    - name: exp
      function: negative_exponential
      beta: 0.001
  max_cost: 10000.0
output:
  directory: outputs
"""
    with pytest.raises(ConfigError, match="origins_path"):
        load_config(_write_config(tmp_path, content))


def test_invalid_impedance_function(tmp_path: Path):
    content = _VALID.replace("function: linear", "function: gravitacional")
    with pytest.raises(ConfigError, match="impedância"):
        load_config(_write_config(tmp_path, content))


def test_only_one_impedance_raises(tmp_path: Path):
    content = """
data:
  network_path: rede.gpkg
  origins_path: origens.gpkg
  origins_id_column: id
  opportunities_column: opp
  population_column: pop
  analysis_crs: EPSG:31983
analysis:
  impedances:
    - name: lin
      function: linear
      cutoff: 5000.0
  max_cost: 10000.0
output:
  directory: outputs
"""
    with pytest.raises(ConfigError, match="duas"):
        load_config(_write_config(tmp_path, content))


def test_negative_exponential_requires_beta(tmp_path: Path):
    content = _VALID.replace(
        "- name: exp\n      function: negative_exponential\n      beta: 0.001",
        "- name: exp\n      function: negative_exponential",
    )
    with pytest.raises(ConfigError, match="beta"):
        load_config(_write_config(tmp_path, content))


def test_duplicate_impedance_names(tmp_path: Path):
    content = _VALID.replace("- name: exp", "- name: lin")
    with pytest.raises(ConfigError, match="únicos"):
        load_config(_write_config(tmp_path, content))
