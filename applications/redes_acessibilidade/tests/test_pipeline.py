"""Testes do pipeline completo."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from redes_acessibilidade.pipeline import run_pipeline


def test_pipeline_generates_all_products(pipeline_project: Path):
    result = run_pipeline(pipeline_project / "config" / "test.yml")

    assert "output_dir" in result
    assert "outputs" in result
    assert "report" in result

    output_dir = Path(result["output_dir"])
    assert output_dir.exists()

    # Check key files
    assert (output_dir / "origens_acessibilidade.gpkg").exists()
    assert (output_dir / "relatorio_topologia.json").exists()
    assert (output_dir / "comparacao_rede_euclidiana.csv").exists()
    assert (output_dir / "tabela_desigualdades.csv").exists()
    assert (output_dir / "caminhos_minimos_origens.csv").exists()
    assert (output_dir / "relatorio_acessibilidade.json").exists()
    assert (output_dir / "manifesto_execucao.json").exists()

    # Validate topology report content
    topo = json.loads((output_dir / "relatorio_topologia.json").read_text())
    assert "n_edges" in topo
    assert "n_nodes" in topo
    assert "n_components" in topo
    assert topo["n_edges"] > 0

    # Validate report content
    report = result["report"]
    assert report["n_origins"] == 4
    assert len(report["impedances"]) == 2
    assert "inequality" in report
    assert "topology" in report

    # Validate manifesto has sha256
    manifest = json.loads((output_dir / "manifesto_execucao.json").read_text())
    assert "outputs" in manifest
    assert all(len(item["sha256"]) == 64 for item in manifest["outputs"])


def test_pipeline_accessibility_columns(pipeline_project: Path):
    """As colunas de acessibilidade devem estar no GeoPackage de saída."""
    import geopandas as gpd

    result = run_pipeline(pipeline_project / "config" / "test.yml")
    output_dir = Path(result["output_dir"])
    gdf = gpd.read_file(output_dir / "origens_acessibilidade.gpkg")
    assert "acess_linear_5km" in gdf.columns
    assert "acess_exp_neg" in gdf.columns


def test_pipeline_two_impedances(pipeline_project: Path):
    """Os resultados das duas funções de impedância devem diferir."""
    import geopandas as gpd

    result = run_pipeline(pipeline_project / "config" / "test.yml")
    output_dir = Path(result["output_dir"])
    gdf = gpd.read_file(output_dir / "origens_acessibilidade.gpkg")
    # The two impedance functions should produce different values
    assert not (gdf["acess_linear_5km"] == gdf["acess_exp_neg"]).all()


def test_pipeline_detour_ratio_positive(pipeline_project: Path):
    """Razão de desvio deve ser >= 1 (rede nunca é mais curta que linha reta)."""
    import pandas as pd

    result = run_pipeline(pipeline_project / "config" / "test.yml")
    output_dir = Path(result["output_dir"])
    df = pd.read_csv(output_dir / "comparacao_rede_euclidiana.csv")
    valid = df.dropna(subset=["detour_ratio"])
    assert (valid["detour_ratio"] >= 1.0 - 1e-6).all()
