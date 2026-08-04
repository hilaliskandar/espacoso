from __future__ import annotations

"""Pipeline completo de análise de painéis espaciais."""

from pathlib import Path

import numpy as np
import pandas as pd

from .config import load_config, PanelConfig, ModelSpec
from .io import read_panel_data, write_table
from .models import (
    FittedPanel,
    SpatialPanelResult,
    compare_models,
    fit_fe,
    fit_spatial_lag,
    fit_spatial_error,
)
from .panel import build_panel, lag_column, PanelData
from .reporting import write_manifest, write_report
from .weights import build_weights, matrix_diagnostics


def _build_panel_data(raw_df: pd.DataFrame, config: PanelConfig) -> PanelData:
    return build_panel(
        raw_df,
        unit_col=config.unit_col,
        time_col=config.time_col,
        gap_strategy=config.gap_strategy,
        gap_limit=config.gap_limit,
    )


def _run_model(
    spec: ModelSpec,
    panel: PanelData,
    weights_map: dict[str, np.ndarray],
) -> FittedPanel | SpatialPanelResult:
    """Estima um modelo de acordo com sua especificação."""
    if spec.model_type == "fe":
        return fit_fe(
            panel,
            target=spec.target,
            predictors=list(spec.predictors),
            fixed_effects=spec.fixed_effects,
            spec_name=spec.name,
        )

    if not weights_map:
        from .errors import PanelError
        raise PanelError("Nenhuma matriz de pesos disponível para modelo espacial.")

    # Usa a primeira matriz de pesos disponível para o modelo espacial
    W = next(iter(weights_map.values()))

    if spec.model_type == "spatial_lag":
        return fit_spatial_lag(
            panel,
            W=W,
            target=spec.target,
            predictors=list(spec.predictors),
            fixed_effects=spec.fixed_effects,
            spec_name=spec.name,
            dynamic=spec.dynamic,
        )

    return fit_spatial_error(
        panel,
        W=W,
        target=spec.target,
        predictors=list(spec.predictors),
        fixed_effects=spec.fixed_effects,
        spec_name=spec.name,
        dynamic=spec.dynamic,
    )


def run_pipeline(config_path: str | Path) -> list[Path]:
    """Executa o pipeline completo de análise de painel espacial.

    Parameters
    ----------
    config_path:
        Caminho para o arquivo YAML de configuração.

    Returns
    -------
    list[Path]
        Lista de arquivos produzidos.
    """
    config_path = Path(config_path).resolve()
    config = load_config(config_path)
    output = config.output_dir
    output.mkdir(parents=True, exist_ok=True)
    outputs: list[Path] = []

    # 1. Carregar dados
    raw_df = read_panel_data(config)

    # 2. Construir painel
    panel = _build_panel_data(raw_df, config)

    # 3. Criar defasagens temporais se necessário
    for spec in config.models:
        if spec.dynamic:
            panel = PanelData(
                data=lag_column(panel.data, spec.target, n_lags=spec.n_lags),
                unit_col=panel.unit_col,
                time_col=panel.time_col,
                balanced=panel.balanced,
                n_units=panel.n_units,
                n_periods=panel.n_periods,
                missing_cells=panel.missing_cells,
            )
            break  # uma passagem é suficiente para criar lag1

    # 4. Construir matrizes de pesos
    ids = panel.data.index.get_level_values(0).unique().tolist()
    weights_map: dict[str, np.ndarray] = {}
    for wspec in config.weights:
        weights_map[wspec.name] = build_weights(wspec, ids)

    # 5. Salvar diagnóstico do painel
    balance_info = {
        "balanced": [panel.balanced],
        "n_units": [panel.n_units],
        "n_periods": [panel.n_periods],
        "missing_cells": [panel.missing_cells],
        "gap_strategy": [config.gap_strategy],
    }
    balance_path = output / "diagnostico_painel.csv"
    write_table(pd.DataFrame(balance_info), balance_path)
    outputs.append(balance_path)

    # 6. Salvar diagnóstico das matrizes de pesos
    if weights_map:
        w_diag = pd.DataFrame(
            matrix_diagnostics(w, name=n) for n, w in weights_map.items()
        )
        w_diag_path = output / "diagnostico_pesos.csv"
        write_table(w_diag, w_diag_path)
        outputs.append(w_diag_path)

    # 7. Estimar modelos
    fe_results: list[FittedPanel] = []
    spatial_results: list[SpatialPanelResult] = []
    all_model_results: list[FittedPanel | SpatialPanelResult] = []

    for spec in config.models:
        result = _run_model(spec, panel, weights_map)
        all_model_results.append(result)
        if isinstance(result, FittedPanel):
            fe_results.append(result)
        else:
            spatial_results.append(result)

    # 8. Tabelas de coeficientes
    coef_rows: list[dict] = []
    for result in all_model_results:
        if isinstance(result, FittedPanel):
            params = result.result.params
            bse = result.result.bse
            pval = result.result.pvalues
            for name, coef, se, p in zip(result.predictors, params, bse, pval):
                coef_rows.append({
                    "model": result.spec_name,
                    "model_type": "fe_ols",
                    "predictor": name,
                    "coef": round(float(coef), 6),
                    "std_err": round(float(se), 6),
                    "p_value": round(float(p), 6),
                    "spatial_param": "",
                    "spatial_coef": float("nan"),
                })
        else:
            for pname, coef, se, p in zip(
                result.param_names, result.params, result.std_errors, result.p_values
            ):
                coef_rows.append({
                    "model": result.spec_name,
                    "model_type": result.model_type,
                    "predictor": pname,
                    "coef": round(float(coef), 6),
                    "std_err": round(float(se), 6),
                    "p_value": round(float(p), 6),
                    "spatial_param": result.spatial_param_name,
                    "spatial_coef": round(float(result.rho_or_lambda), 6),
                })

    coef_path = output / "coeficientes.csv"
    write_table(pd.DataFrame(coef_rows), coef_path)
    outputs.append(coef_path)

    # 9. Comparação de modelos
    if fe_results and spatial_results:
        comparison = compare_models(fe_results[0], spatial_results)
    elif fe_results:
        comparison = compare_models(fe_results[0], [])
    else:
        # Somente modelos espaciais — criar FE vazio para comparação não se aplica
        comparison = pd.DataFrame(
            {
                "spec_name": [r.spec_name for r in spatial_results],
                "model_type": [r.model_type for r in spatial_results],
                "r_squared": [round(r.r_squared, 4) for r in spatial_results],
            }
        )

    comparison_path = output / "comparacao_modelos.csv"
    write_table(comparison, comparison_path)
    outputs.append(comparison_path)

    # 10. Identificação e notas
    id_notes_rows: list[dict] = []
    for sr in spatial_results:
        id_notes_rows.append({
            "model": sr.spec_name,
            "model_type": sr.model_type,
            "identification_note": sr.identification_note,
        })
    if id_notes_rows:
        notes_path = output / "notas_identificacao.csv"
        write_table(pd.DataFrame(id_notes_rows), notes_path)
        outputs.append(notes_path)

    # 11. Relatório
    primary_fe = fe_results[0] if fe_results else None
    report_path = output / "relatorio.md"
    if primary_fe is not None:
        write_report(report_path, comparison, primary_fe, spatial_results, config.alpha)
        outputs.append(report_path)

    # 12. Manifesto
    manifest_path = output / "manifesto.json"
    inputs: list[Path] = [config.input_path] + [ws.path for ws in config.weights]
    write_manifest(
        manifest_path,
        config_path=config_path,
        inputs=inputs,
        outputs=outputs,
        seed=config.seed,
    )
    outputs.append(manifest_path)

    return outputs
