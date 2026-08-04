"""Testes de integração do ponto de entrada (run.py)."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from projeto_aplicado.run import main


def test_main_loads_config(demo_config, tmp_path, capsys):
    """CLI deve carregar configuração e imprimir título do projeto."""
    cfg_path = tmp_path / "projeto.yml"
    with cfg_path.open("w") as fh:
        yaml.dump(demo_config, fh)

    exit_code = main(["--config", str(cfg_path)])
    assert exit_code == 0

    captured = capsys.readouterr()
    assert "Projeto de Teste" in captured.out


def test_main_missing_config(tmp_path):
    """CLI com arquivo inexistente deve levantar FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        main(["--config", str(tmp_path / "nao_existe.yml")])
