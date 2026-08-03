from pathlib import Path

import pytest

from dados_espaciais.config import load_config
from dados_espaciais.errors import ConfigError


def test_config_requires_mandatory_fields(tmp_path: Path):
    path = tmp_path / "bad.yml"
    path.write_text("paths: {}", encoding="utf-8")
    with pytest.raises(ConfigError, match="paths.spatial"):
        load_config(path)


def test_config_loads_valid_project(pipeline_project: Path):
    config, path = load_config(pipeline_project / "config" / "test.yml")
    assert config["crs"]["analysis"] == "EPSG:31983"
    assert path.is_absolute()
