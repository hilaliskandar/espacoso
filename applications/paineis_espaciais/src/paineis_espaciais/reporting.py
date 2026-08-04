from __future__ import annotations

"""Relatórios textuais e de manifesto para painéis espaciais."""

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from .models import FittedPanel, SpatialPanelResult


def _fmt(value: object) -> str:
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def write_report(
    path: Path,
    comparison: pd.DataFrame,
    fe_result: FittedPanel,
    spatial_results: list[SpatialPanelResult],
    alpha: float,
) -> None:
    """Escreve relatório Markdown com comparação de modelos e diagnósticos."""
    lines: list[str] = []
    lines.append("# Relatório — Painéis Espaciais e Dinâmica Territorial\n")
    lines.append(f"Gerado em: {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}\n")
    lines.append(f"Nível de significância: α = {alpha}\n")

    lines.append("## Comparação de Modelos\n")
    lines.append(comparison.to_markdown(index=False))
    lines.append("\n")

    # Coeficientes FE
    lines.append(f"## Efeitos Fixos OLS — {fe_result.spec_name}\n")
    lines.append(f"- Variável dependente: `{fe_result.target}`\n")
    lines.append(f"- Preditores: {', '.join(fe_result.predictors)}\n")
    lines.append(f"- Efeitos fixos: `{fe_result.fixed_effects}`\n")
    lines.append(f"- Observações: {fe_result.n_obs}\n")
    lines.append(f"- R²: {_fmt(fe_result.result.rsquared)}\n")

    lines.append("\n### Coeficientes\n")
    params = fe_result.result.params
    bse = fe_result.result.bse
    pval = fe_result.result.pvalues
    coef_df = pd.DataFrame({
        "predictor": fe_result.predictors,
        "coef": params.tolist(),
        "std_err": bse.tolist(),
        "p_value": pval.tolist(),
        "sig": ["*" if p < alpha else "" for p in pval],
    })
    lines.append(coef_df.to_markdown(index=False))
    lines.append("\n")

    # Modelos espaciais
    for sr in spatial_results:
        lines.append(f"## {sr.model_type.replace('_', ' ').title()} — {sr.spec_name}\n")
        lines.append(f"- Efeitos fixos: `{sr.fixed_effects}`\n")
        lines.append(f"- Observações: {sr.n_obs}\n")
        lines.append(f"- R²: {_fmt(sr.r_squared)}\n")
        lines.append(f"- {sr.spatial_param_name}: {_fmt(sr.rho_or_lambda)}\n")
        lines.append(f"- Dinâmico: {sr.dynamic}\n")
        lines.append(f"\n**Nota de identificação:** {sr.identification_note}\n")

        if len(sr.params) > 0:
            coef_df2 = pd.DataFrame({
                "predictor": sr.param_names,
                "coef": sr.params.tolist(),
                "std_err": sr.std_errors.tolist(),
                "p_value": sr.p_values.tolist(),
                "sig": ["*" if p < alpha else "" for p in sr.p_values],
            })
            lines.append("\n### Coeficientes\n")
            lines.append(coef_df2.to_markdown(index=False))
            lines.append("\n")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def write_manifest(
    path: Path,
    *,
    config_path: Path,
    inputs: list[Path],
    outputs: list[Path],
    seed: int,
) -> None:
    """Escreve manifesto JSON com proveniência da análise."""
    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "config": str(config_path),
        "seed": seed,
        "inputs": [str(p) for p in inputs],
        "outputs": [str(p) for p in outputs],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
