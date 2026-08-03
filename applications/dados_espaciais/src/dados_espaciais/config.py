from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .errors import ConfigError


_REQUIRED_PATHS = (
    ("paths", "spatial"),
    ("paths", "table"),
    ("paths", "output_dir"),
    ("keys", "spatial"),
    ("keys", "table"),
    ("crs", "analysis"),
    ("map", "column"),
    ("map", "output"),
)


def load_config(path: str | Path) -> tuple[dict[str, Any], Path]:
    config_path = Path(path).resolve()
    if not config_path.exists():
        raise ConfigError(f"Configuração não encontrada: {config_path}")
    data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ConfigError("A configuração deve ser um objeto YAML.")
    for section, key in _REQUIRED_PATHS:
        if section not in data or key not in data[section]:
            raise ConfigError(f"Campo obrigatório ausente: {section}.{key}")
    return data, config_path


def resolve_path(value: str, config_path: Path) -> Path:
    candidate = Path(value)
    if not candidate.is_absolute():
        candidate = (config_path.parent / candidate).resolve()
    return candidate
