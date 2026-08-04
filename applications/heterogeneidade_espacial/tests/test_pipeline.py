from __future__ import annotations

import json
from pathlib import Path

from heterogeneidade_espacial.pipeline import run_pipeline


def test_pipeline_generates_expected_outputs(demo_config):
    config_path, output = demo_config
    products = run_pipeline(config_path)
    names = {p.name for p in products}

    expected = {
        "coeficientes_globais.csv",
        "resumo_modelos.csv",
        "vif_global.csv",
        "coeficientes_gwr.csv",
        "variabilidade_gwr.csv",
        "colinearidade_local_gwr.csv",
        "comparacao_modelos.csv",
        "heterogeneidade_espacial.gpkg",
        "relatorio.md",
        "manifesto.json",
        "mapa_residuos_ols.png",
        "mapa_residuos_gwr.png",
        "comparacao_aic.png",
        "comparacao_r2.png",
    }
    assert expected.issubset(names), f"Missing: {expected - names}"

    manifest = json.loads((output / "manifesto.json").read_text(encoding="utf-8"))
    assert manifest["seed"] == 42
    assert len(manifest["outputs"]) >= 1
