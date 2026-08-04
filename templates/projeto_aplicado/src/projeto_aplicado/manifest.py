"""Geração do manifesto de execução com hashes e versões."""

from __future__ import annotations

import hashlib
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def sha256_file(path: str | Path) -> str:
    """Retorna o hash SHA-256 hexadecimal de um arquivo."""
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def build_manifest(
    config: dict[str, Any],
    data_files: list[str | Path],
    output_files: list[str | Path],
    warnings: list[str] | None = None,
) -> dict[str, Any]:
    """Constrói o manifesto de execução.

    Parameters
    ----------
    config:
        Configuração efetiva usada na execução.
    data_files:
        Arquivos de dados de entrada para registro de hashes.
    output_files:
        Arquivos de saída para registro de hashes.
    warnings:
        Avisos e limitações da execução.

    Returns
    -------
    dict
        Manifesto serializado como dicionário.
    """
    packages = _installed_packages()

    data_hashes = {}
    for f in data_files:
        p = Path(f)
        data_hashes[str(p)] = sha256_file(p) if p.exists() else "arquivo ausente"

    output_hashes = {}
    for f in output_files:
        p = Path(f)
        output_hashes[str(p)] = sha256_file(p) if p.exists() else "arquivo ausente"

    return {
        "data_execucao": datetime.now(tz=timezone.utc).isoformat(),
        "python_version": sys.version,
        "plataforma": platform.platform(),
        "configuracao": config,
        "pacotes": packages,
        "hashes_dados": data_hashes,
        "hashes_saida": output_hashes,
        "avisos": warnings or [],
    }


def save_manifest(manifest: dict[str, Any], path: str | Path) -> Path:
    """Salva o manifesto em JSON."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=2)
    return path


def _installed_packages() -> dict[str, str]:
    try:
        import importlib.metadata as meta

        return {d.name: d.version for d in meta.distributions()}
    except Exception:  # pragma: no cover
        return {}
