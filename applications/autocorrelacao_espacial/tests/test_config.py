from pathlib import Path

import pytest

from autocorrelacao_espacial.config import ConfigError, load_config


def test_load_demo_config():
    path = Path(__file__).resolve().parents[1] / "config" / "demo.yml"
    config = load_config(path)
    assert config.primary_weight == "rook"
    assert len(config.weights) == 4
    assert config.weights[2].k == 4


def test_reject_duplicate_weight_names(tmp_path):
    path = tmp_path / "bad.yml"
    path.write_text(
        """
data:
  path: x.gpkg
  id_column: id
  value_column: value
  analysis_crs: EPSG:3857
analysis:
  weights:
    - {name: same, type: rook}
    - {name: same, type: queen}
output: {directory: out}
""",
        encoding="utf-8",
    )
    with pytest.raises(ConfigError, match="únicos"):
        load_config(path)


def test_reject_invalid_permutations(tmp_path):
    path = tmp_path / "bad.yml"
    path.write_text(
        """
data:
  path: x.gpkg
  id_column: id
  value_column: value
  analysis_crs: EPSG:3857
analysis:
  permutations: 9
  weights:
    - {name: rook, type: rook}
output: {directory: out}
""",
        encoding="utf-8",
    )
    with pytest.raises(ConfigError, match="pelo menos 19"):
        load_config(path)
