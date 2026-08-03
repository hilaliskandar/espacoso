from pathlib import Path

import pytest

from diagnostico_ols.config import load_config
from diagnostico_ols.errors import ConfigError


def _write(path: Path, text: str) -> Path:
    path.write_text(text, encoding="utf-8")
    return path


def test_load_config_resolves_paths(tmp_path: Path):
    config = _write(
        tmp_path / "config.yml",
        """
data: {path: data.gpkg, id_column: id}
models:
  - {name: m1, target: y, predictors: [x1]}
weights:
  - {name: rook, path: w.csv}
primary_model: m1
primary_weights: rook
output: {dir: out}
permutations: 99
""",
    )
    loaded = load_config(config)
    assert loaded.input_path == (tmp_path / "data.gpkg").resolve()
    assert loaded.weights[0].path == (tmp_path / "w.csv").resolve()
    assert loaded.output_dir == (tmp_path / "out").resolve()


def test_rejects_unknown_primary_model(tmp_path: Path):
    config = _write(
        tmp_path / "config.yml",
        """
data: {path: data.gpkg, id_column: id}
models:
  - {name: m1, target: y, predictors: [x1]}
weights:
  - {name: rook, path: w.csv}
primary_model: missing
primary_weights: rook
output: {dir: out}
permutations: 99
""",
    )
    with pytest.raises(ConfigError):
        load_config(config)


def test_rejects_too_few_permutations(tmp_path: Path):
    config = _write(
        tmp_path / "config.yml",
        """
data: {path: data.gpkg, id_column: id}
models:
  - {name: m1, target: y, predictors: [x1]}
weights:
  - {name: rook, path: w.csv}
primary_model: m1
primary_weights: rook
output: {dir: out}
permutations: 10
""",
    )
    with pytest.raises(ConfigError):
        load_config(config)
