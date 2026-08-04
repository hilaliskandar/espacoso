"""Testes do módulo de configuração."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from projeto_aplicado.config import load_config


def test_load_valid_config(demo_config, tmp_path):
    """Configuração válida deve ser carregada sem erros."""
    cfg_path = tmp_path / "projeto.yml"
    with cfg_path.open("w") as fh:
        yaml.dump(demo_config, fh)

    cfg = load_config(cfg_path)
    assert cfg["projeto"]["titulo"] == "Projeto de Teste"
    assert cfg["data"]["id_column"] == "id"
    assert cfg["reproducao"]["seed"] == 42


def test_load_missing_file(tmp_path):
    """Arquivo inexistente deve levantar FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        load_config(tmp_path / "nao_existe.yml")


def test_load_config_todo_value(demo_config, tmp_path):
    """Campo com marcador TODO deve levantar ValueError."""
    demo_config["projeto"]["titulo"] = "TODO: preencher"
    cfg_path = tmp_path / "projeto.yml"
    with cfg_path.open("w") as fh:
        yaml.dump(demo_config, fh)

    with pytest.raises(ValueError, match="TODO"):
        load_config(cfg_path)


def test_load_config_missing_section(demo_config, tmp_path):
    """Seção obrigatória ausente deve levantar KeyError."""
    del demo_config["reproducao"]
    cfg_path = tmp_path / "projeto.yml"
    with cfg_path.open("w") as fh:
        yaml.dump(demo_config, fh)

    with pytest.raises(KeyError, match="reproducao"):
        load_config(cfg_path)


def test_load_config_missing_field(demo_config, tmp_path):
    """Campo obrigatório ausente deve levantar KeyError."""
    del demo_config["data"]["analysis_crs"]
    cfg_path = tmp_path / "projeto.yml"
    with cfg_path.open("w") as fh:
        yaml.dump(demo_config, fh)

    with pytest.raises(KeyError):
        load_config(cfg_path)
