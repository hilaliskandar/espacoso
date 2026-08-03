from __future__ import annotations

from pathlib import Path

import pandas as pd

from .cartography import influence_map, residual_map
from .config import load_config
from .diagnostics import classical_diagnostics, influence_table, spatial_diagnostics
from .io import read_geodata, write_geodata
from .modeling import coefficient_table, fit_model, model_summary, vif_table
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

    coefficient_frames: list[pd.DataFrame] = []
    vif_frames: list[pd.DataFrame] = []
    model_rows: list[dict] = []
    classical_rows: list[dict] = []
    spatial_rows: list[dict] = []
    influence_frames: list[pd.DataFrame] = []
    outputs: list[Path] = []

    result_gdf = gdf.copy()
    for model_index, spec in enumerate(config.models):
        fitted = fit_model(gdf, spec)
        coefficient_frames.append(coefficient_table(fitted))
        vif_frames.append(vif_table(fitted))
        model_rows.append(model_summary(fitted))
        classical_rows.append(classical_diagnostics(fitted))
        influence = influence_table(fitted, ids)
        influence_frames.append(influence)

        safe = spec.name.replace(" ", "_")
        result_gdf[f"fitted_{safe}"] = fitted.conventional.fittedvalues.to_numpy()
        result_gdf[f"residual_{safe}"] = fitted.conventional.resid.to_numpy()
        result_gdf[f"cook_{safe}"] = influence["cooks_distance"].to_numpy()
        result_gdf[f"leverage_{safe}"] = influence["leverage"].to_numpy()

        residual_path = output / f"mapa_residuos_{safe}.png"
        residual_map(result_gdf, f"residual_{safe}", residual_path, f"Resíduos OLS — {spec.name}")
        outputs.append(residual_path)
        influence_path = output / f"mapa_influencia_{safe}.png"
        influence_map(result_gdf, f"cook_{safe}", influence_path, f"Distância de Cook — {spec.name}")
        outputs.append(influence_path)

        for weight_index, weights in enumerate(weights_by_name.values()):
            spatial_rows.append(
                spatial_diagnostics(
                    fitted,
                    weights,
                    permutations=config.permutations,
                    seed=config.seed + 1000 * model_index + weight_index,
                )
            )

    coefficients = pd.concat(coefficient_frames, ignore_index=True)
    vif = pd.concat(vif_frames, ignore_index=True) if vif_frames else pd.DataFrame()
    summaries = pd.DataFrame(model_rows)
    classical = pd.DataFrame(classical_rows)
    spatial = pd.DataFrame(spatial_rows)
    influence_all = pd.concat(influence_frames, ignore_index=True)
    weights_summary = pd.DataFrame(matrix_diagnostics(w) for w in weights_by_name.values())

    tables = {
        "coeficientes.csv": coefficients,
        "resumo_modelos.csv": summaries,
        "diagnosticos_classicos.csv": classical,
        "diagnosticos_espaciais.csv": spatial,
        "vif.csv": vif,
        "influencia.csv": influence_all,
        "diagnostico_pesos.csv": weights_summary,
    }
    for filename, frame in tables.items():
        path = output / filename
        frame.to_csv(path, index=False)
        outputs.append(path)

    gpkg = output / "diagnostico_ols.gpkg"
    write_geodata(result_gdf, gpkg, layer="diagnostico")
    outputs.append(gpkg)

    report = output / "relatorio.md"
    write_report(report, summaries, coefficients, classical, spatial, vif, config.alpha)
    outputs.append(report)

    manifest = output / "manifesto.json"
    inputs = [config.input_path, *(spec.path for spec in config.weights)]
    write_manifest(
        manifest,
        config_path=config_path,
        inputs=inputs,
        outputs=outputs,
        seed=config.seed,
        permutations=config.permutations,
    )
    outputs.append(manifest)
    return outputs
