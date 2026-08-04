from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


def write_report(
    path: Path,
    comparison: pd.DataFrame,
    variability_frames: dict[str, pd.DataFrame],
    alpha: float,
) -> None:
    lines: list[str] = [
        "# Relatório: Heterogeneidade Espacial (GWR / MGWR)",
        "",
        f"Gerado em: {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}",
        f"Nível de significância: α = {alpha}",
        "",
        "## Comparação de Modelos",
        "",
    ]

    for col in comparison.columns:
        if comparison[col].dtype == float:
            comparison[col] = comparison[col].map(lambda v: f"{v:.4f}" if pd.notna(v) else "—")
    lines.append(comparison.to_markdown(index=False))
    lines.append("")

    for model_name, var_df in variability_frames.items():
        lines += [
            f"## Variabilidade dos Coeficientes Locais — {model_name}",
            "",
            "> Os coeficientes locais variam espacialmente.",
            "> IQR elevado indica maior heterogeneidade.",
            "> Risco de sobreinterpretação: coeficientes com incerteza alta (std elevado)",
            "> não devem ser interpretados como efeitos causais locais definitivos.",
            "",
        ]
        lines.append(var_df.to_markdown(index=False))
        lines.append("")

    lines += [
        "## Notas Metodológicas",
        "",
        "- A banda (bandwidth) foi selecionada via critério AICc por padrão.",
        "- Kernel bisquare adaptativo é o padrão; verifique a configuração.",
        "- Coeficientes locais devem ser interpretados com cautela:",
        "  múltiplas estimativas aumentam o risco de falsos positivos.",
        "- Compare sempre com o modelo global (OLS) antes de concluir heterogeneidade.",
        "- Use os intervalos de confiança locais para avaliar a incerteza.",
        "",
    ]

    path.write_text("\n".join(lines), encoding="utf-8")


def write_manifest(
    path: Path,
    config_path: Path,
    inputs: list[Path],
    outputs: list[Path],
    seed: int,
) -> None:
    manifest = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "config": str(config_path),
        "seed": seed,
        "inputs": [str(p) for p in inputs],
        "outputs": [str(p) for p in outputs],
    }
    path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
