"""Carregamento e validação da configuração do projeto aplicado."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def load_config(path: str | Path) -> dict[str, Any]:
    """Carrega e valida o arquivo YAML de configuração.

    Parameters
    ----------
    path:
        Caminho para o arquivo YAML de configuração.

    Returns
    -------
    dict
        Configuração validada.

    Raises
    ------
    FileNotFoundError
        Se o arquivo não existir.
    KeyError
        Se campos obrigatórios estiverem ausentes.
    ValueError
        Se campos obrigatórios contiverem o marcador 'TODO'.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Arquivo de configuração não encontrado: {path}")

    with path.open(encoding="utf-8") as fh:
        cfg: dict[str, Any] = yaml.safe_load(fh)

    _validate_required(cfg)
    return cfg


_REQUIRED_FIELDS = [
    ("projeto", "titulo"),
    ("data", "path"),
    ("data", "id_column"),
    ("data", "value_column"),
    ("data", "analysis_crs"),
    ("reproducao", "seed"),
]


def _validate_required(cfg: dict[str, Any]) -> None:
    for section, key in _REQUIRED_FIELDS:
        if section not in cfg:
            raise KeyError(f"Seção obrigatória ausente na configuração: '{section}'")
        value = cfg[section].get(key)
        if value is None:
            raise KeyError(
                f"Campo obrigatório ausente na configuração: '{section}.{key}'"
            )
        if isinstance(value, str) and value.strip().upper().startswith("TODO"):
            raise ValueError(
                f"Campo '{section}.{key}' ainda contém marcador TODO. "
                "Preencha a configuração antes de executar."
            )
