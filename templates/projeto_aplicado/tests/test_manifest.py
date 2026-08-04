"""Testes do módulo de manifesto."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from projeto_aplicado.manifest import (
    build_manifest,
    save_manifest,
    sha256_file,
)


def test_sha256_file(tmp_path):
    """Hash SHA-256 deve ser reproduzível e correto."""
    f = tmp_path / "arquivo.txt"
    f.write_text("conteudo de teste", encoding="utf-8")

    expected = hashlib.sha256(b"conteudo de teste").hexdigest()
    assert sha256_file(f) == expected


def test_sha256_determinism(tmp_path):
    """Hash deve ser idêntico em chamadas repetidas."""
    f = tmp_path / "arquivo.bin"
    f.write_bytes(b"\x00\x01\x02" * 100)
    assert sha256_file(f) == sha256_file(f)


def test_build_manifest_contains_required_fields(demo_config, tmp_path):
    """Manifesto deve conter campos mínimos obrigatórios."""
    data_file = tmp_path / "dados.gpkg"
    data_file.write_bytes(b"fake")

    manifest = build_manifest(
        config=demo_config,
        data_files=[data_file],
        output_files=[],
        warnings=["aviso de teste"],
    )

    assert "data_execucao" in manifest
    assert "python_version" in manifest
    assert "hashes_dados" in manifest
    assert "hashes_saida" in manifest
    assert "avisos" in manifest
    assert manifest["avisos"] == ["aviso de teste"]


def test_save_and_reload_manifest(demo_config, tmp_path):
    """Manifesto salvo em JSON deve ser recarregado com os mesmos valores."""
    manifest = build_manifest(
        config=demo_config,
        data_files=[],
        output_files=[],
    )
    out = tmp_path / "outputs" / "manifesto.json"
    save_manifest(manifest, out)

    assert out.exists()
    with out.open() as fh:
        loaded = json.load(fh)

    assert loaded["python_version"] == manifest["python_version"]
    assert loaded["configuracao"]["projeto"]["titulo"] == "Projeto de Teste"


def test_manifest_missing_data_file(demo_config, tmp_path):
    """Arquivo de dados ausente não deve levantar erro; registra 'arquivo ausente'."""
    manifest = build_manifest(
        config=demo_config,
        data_files=[tmp_path / "nao_existe.gpkg"],
        output_files=[],
    )
    values = list(manifest["hashes_dados"].values())
    assert values[0] == "arquivo ausente"
