"""Pipeline principal de econometria espacial."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from .config import load_config
from .diagnostics import fit_comparison, residual_diagnostics, verify_impacts_numerically
from .impacts import compute_impacts, impacts_table
from .io import read_geodata, write_geodata
from .models import coefficient_table, fit_spatial_model, model_summary
from .reporting import write_manifest, write_report
from .weights import load_weights, matrix_diagnostics


def run_pipeline(config_path: str | Path) -> list[Path]:
    config_path = Path(config_path).resolve()
    config = load_config(config_path)
    output = config.output_dir
    output.mkdir(parents=True, exist_ok=True)

    gdf = read_geodata(config)
    ids = gdf[config.id_column].astype(str).tolist()
    weights_by_name = {spec.name: load_weights(spec, ids) for spec in config.weights}

    results = []
    coef_frames: list[pd.DataFrame] = []
    summary_rows: list[dict] = []

    for spec in config.models:
        weights = weights_by_name[spec.weights_name]
        result = fit_spatial_model(gdf, spec, weights)
        results.append(result)
        coef_frames.append(coefficient_table(result))
        summary_rows.append(model_summary(result))

    coefficients = pd.concat(coef_frames, ignore_index=True)
    summaries = pd.DataFrame(summary_rows)

    # Impactos
    imp_table = impacts_table(results)
    all_decomps = [d for r in results for d in compute_impacts(r)]
    impact_check = verify_impacts_numerically(all_decomps)

    # Diagnósticos de resíduos
    primary_weights = weights_by_name[config.primary_weights]
    resid_rows: list[dict] = []
    for r in results:
        resid_rows.append(
            residual_diagnostics(
                r,
                primary_weights,
                permutations=config.permutations,
                seed=config.seed,
            )
        )
    residual_diag = pd.DataFrame(resid_rows)

    # Comparação de ajuste
    comparison = fit_comparison(results)

    # Diagnósticos das matrizes
    weights_summary = pd.DataFrame(matrix_diagnostics(w) for w in weights_by_name.values())

    outputs: list[Path] = []
    tables = {
        "coeficientes.csv": coefficients,
        "resumo_modelos.csv": summaries,
        "comparacao_ajuste.csv": comparison,
        "impactos.csv": imp_table,
        "verificacao_impactos.csv": impact_check,
        "diagnosticos_residuos.csv": residual_diag,
        "diagnostico_pesos.csv": weights_summary,
    }
    for filename, frame in tables.items():
        path = output / filename
        frame.to_csv(path, index=False)
        outputs.append(path)

    # GeoPackage com resíduos e ajustados
    result_gdf = gdf.copy()
    for r in results:
        safe = r.spec.name.replace(" ", "_")
        result_gdf[f"fitted_{safe}"] = r.fitted
        result_gdf[f"residual_{safe}"] = r.residuals

    gpkg = output / "econometria_espacial.gpkg"
    write_geodata(result_gdf, gpkg, layer="resultados")
    outputs.append(gpkg)

    report = output / "relatorio.md"
    write_report(report, comparison, coefficients, imp_table, residual_diag, impact_check, config.alpha)
    outputs.append(report)

    manifest = output / "manifesto.json"
    inputs = [config.input_path, *(spec.path for spec in config.weights)]
    write_manifest(manifest, config_path=config_path, inputs=inputs, outputs=outputs,
                   seed=config.seed, permutations=config.permutations)
    outputs.append(manifest)
    return outputs
