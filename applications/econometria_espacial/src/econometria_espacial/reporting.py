"""Geração de relatório Markdown para econometria_espacial."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


def _fmt(value: object, precision: int = 4) -> str:
    if isinstance(value, float):
        if value != value:  # nan
            return "—"
        return f"{value:.{precision}f}"
    if value is None:
        return "—"
    return str(value)


def _df_to_md(df: pd.DataFrame, float_cols: list[str] | None = None) -> str:
    if df.empty:
        return "_Sem dados._\n"
    lines = ["| " + " | ".join(str(c) for c in df.columns) + " |"]
    lines.append("| " + " | ".join("---" for _ in df.columns) + " |")
    for _, row in df.iterrows():
        cells = []
        for col in df.columns:
            v = row[col]
            if isinstance(v, float):
                cells.append(_fmt(v))
            else:
                cells.append(str(v))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines) + "\n"


def write_report(
    path: Path,
    fit_comparison: pd.DataFrame,
    coefficients: pd.DataFrame,
    impacts: pd.DataFrame,
    residual_diag: pd.DataFrame,
    impact_check: pd.DataFrame,
    alpha: float,
) -> None:
    lines: list[str] = [
        "# Relatório — Econometria Espacial\n",
        f"_Gerado em {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}_\n",
        "---\n",
        "## 1. Comparação de Ajuste\n",
        _df_to_md(fit_comparison),
        "## 2. Coeficientes Estimados\n",
        _df_to_md(coefficients),
        "## 3. Decomposição de Impactos\n",
        "> **Nota**: coeficientes autorregressivos (ρ, λ) *não* são interpretados como "
        "coeficientes OLS. Para SAR e SDM, os impactos diretos e indiretos derivam da "
        "inversão espacial (I-ρW)⁻¹ e refletem feedback entre vizinhos.\n",
        _df_to_md(impacts),
        "## 4. Diagnósticos de Resíduos\n",
        _df_to_md(residual_diag),
        "## 5. Verificação Numérica dos Impactos\n",
        _df_to_md(impact_check),
        "---\n",
        "### Distinção conceitual\n",
        "- **Associação**: correlação entre variável e outcome sem controle.\n",
        "- **Mecanismo**: canal pelo qual a variável afeta o outcome (direto vs. indireto).\n",
        "- **Causalidade**: requer identificação exógena (IV, RDD, experimento).\n",
        "Os modelos estimados descrevem mecanismos plausíveis, não relações causais.\n",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def write_manifest(
    path: Path,
    config_path: Path,
    inputs: list[Path],
    outputs: list[Path],
    seed: int,
    permutations: int,
) -> None:
    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "config": str(config_path),
        "seed": seed,
        "permutations": permutations,
        "inputs": [str(p) for p in inputs],
        "outputs": [str(p) for p in outputs],
    }
    path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
