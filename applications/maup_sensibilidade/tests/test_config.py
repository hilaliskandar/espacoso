from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from maup_sensibilidade.config import ConfigError, load_config


def _write_config(tmp_path: Path, content: str) -> Path:
    p = tmp_path / "config.yml"
    p.write_text(textwrap.dedent(content), encoding="utf-8")
    return p


def test_load_valid_config(tmp_path: Path) -> None:
    cfg_path = _write_config(
        tmp_path,
        f"""
        data:
          path: {tmp_path}/demo.gpkg
          id_column: id
        variables:
          - renda
        schemes:
          - name: micro
            dissolve_column: null
          - name: meso
            dissolve_column: meso_id
        permutations: 99
        seed: 42
        alpha: 0.05
        output:
          dir: {tmp_path}/out
        """,
    )
    config = load_config(cfg_path)
    assert config.permutations == 99
    assert len(config.schemes) == 2
    assert config.schemes[0].name == "micro"
    assert config.schemes[1].dissolve_column == "meso_id"


def test_missing_required_field_raises(tmp_path: Path) -> None:
    cfg_path = _write_config(
        tmp_path,
        f"""
        data:
          path: {tmp_path}/demo.gpkg
          id_column: id
        schemes:
          - name: micro
          - name: meso
        output:
          dir: {tmp_path}/out
        """,
    )
    with pytest.raises(ConfigError):
        load_config(cfg_path)


def test_single_scheme_raises(tmp_path: Path) -> None:
    cfg_path = _write_config(
        tmp_path,
        f"""
        data:
          path: {tmp_path}/demo.gpkg
          id_column: id
        variables:
          - renda
        schemes:
          - name: micro
        output:
          dir: {tmp_path}/out
        """,
    )
    with pytest.raises(ConfigError, match="ao menos dois"):
        load_config(cfg_path)


def test_duplicate_scheme_names_raise(tmp_path: Path) -> None:
    cfg_path = _write_config(
        tmp_path,
        f"""
        data:
          path: {tmp_path}/demo.gpkg
          id_column: id
        variables:
          - renda
        schemes:
          - name: micro
          - name: micro
        output:
          dir: {tmp_path}/out
        """,
    )
    with pytest.raises(ConfigError, match="duplicado"):
        load_config(cfg_path)


def test_low_permutations_raises(tmp_path: Path) -> None:
    cfg_path = _write_config(
        tmp_path,
        f"""
        data:
          path: {tmp_path}/demo.gpkg
          id_column: id
        variables:
          - renda
        schemes:
          - name: micro
          - name: meso
        permutations: 10
        output:
          dir: {tmp_path}/out
        """,
    )
    with pytest.raises(ConfigError, match="permutations"):
        load_config(cfg_path)
