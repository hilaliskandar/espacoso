from pathlib import Path

import json

from diagnostico_ols.pipeline import run_pipeline


def test_pipeline_generates_expected_outputs(tmp_path: Path, four_grid):
    _, gpkg, weights = four_grid
    output = tmp_path / "out"
    config = tmp_path / "config.yml"
    config.write_text(
        f"""
data:
  path: {gpkg}
  layer: dados
  id_column: id
models:
  - name: baseline
    target: y
    predictors: [x1]
weights:
  - name: line
    path: {weights}
primary_model: baseline
primary_weights: line
permutations: 99
seed: 7
alpha: 0.05
output:
  dir: {output}
""",
        encoding="utf-8",
    )
    products = run_pipeline(config)
    names = {path.name for path in products}
    expected = {
        "coeficientes.csv",
        "resumo_modelos.csv",
        "diagnosticos_classicos.csv",
        "diagnosticos_espaciais.csv",
        "vif.csv",
        "influencia.csv",
        "diagnostico_pesos.csv",
        "diagnostico_ols.gpkg",
        "relatorio.md",
        "manifesto.json",
        "mapa_residuos_baseline.png",
        "mapa_influencia_baseline.png",
    }
    assert expected.issubset(names)
    manifest = json.loads((output / "manifesto.json").read_text(encoding="utf-8"))
    assert manifest["seed"] == 7
    assert len(manifest["outputs"]) == len(products) - 1
