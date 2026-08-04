from __future__ import annotations

"""Geração do relatório Markdown e manifesto de auditoria."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from tabulate import tabulate

from .statistics import MoranResult


def _md_table(df: pd.DataFrame, floatfmt: str = ".4f") -> str:
    return tabulate(df, headers="keys", tablefmt="pipe", floatfmt=floatfmt, showindex=False)


def write_report(
    path: Path,
    descriptive: pd.DataFrame,
    stability: pd.DataFrame,
    conservation: dict[str, dict[str, bool]],
    moran_results: dict[str, dict[str, MoranResult]],
    alpha: float,
) -> None:
    """Escreve relatório Markdown em *path*."""
    lines: list[str] = [
        "# Relatório MAUP — Sensibilidade Territorial\n",
        f"Gerado em: {datetime.now(timezone.utc).isoformat(timespec='seconds')}\n",
        "---\n",
        "## 1. Estatísticas Descritivas por Esquema\n",
        _md_table(descriptive),
        "\n",
        "---\n",
        "## 2. Autocorrelação Espacial (I de Moran)\n",
        _md_table(stability[["variable", "scheme", "moran_i", "expected", "p_value", "significant"]]),
        "\n",
        "---\n",
        "## 3. Estabilidade entre Esquemas\n",
        _md_table(
            stability[
                ["variable", "scheme", "moran_i", "std_i_across_schemes",
                 "range_i_across_schemes", "sign_stable", "significance_stable"]
            ].drop_duplicates()
        ),
        "\n",
        "---\n",
        "## 4. Conservação de Totais\n",
    ]

    conservation_rows: list[dict] = []
    for var, by_scheme in conservation.items():
        for scheme, conserved in by_scheme.items():
            conservation_rows.append({"variável": var, "esquema": scheme, "totais conservados": conserved})
    if conservation_rows:
        lines.append(_md_table(pd.DataFrame(conservation_rows)))
    lines.append("\n")

    lines += [
        "---\n",
        "## 5. Perda de Informação e Falácia Ecológica\n",
        "\n",
        "A agregação territorial reduz o número de observações e suprime a variância "
        "intra-zona, podendo inflacionar artificialmente o I de Moran (efeito MAUP de "
        "escala). Interpretações baseadas em unidades agregadas não devem ser "
        "automaticamente transferidas para unidades individuais (falácia ecológica).\n",
        "\n",
        "Diferenças entre os esquemas devem ser atribuídas com cautela: parte pode "
        "decorrer de escala (número de zonas), parte de zoneamento (configuração das "
        "fronteiras). A tabela de estabilidade acima resume a magnitude e sinal do "
        f"I de Moran (α = {alpha}) para auxiliar nessa atribuição.\n",
    ]

    path.write_text("\n".join(lines), encoding="utf-8")


def _file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def write_manifest(
    path: Path,
    config_path: Path,
    inputs: list[Path],
    outputs: list[Path],
    seed: int,
    permutations: int,
) -> None:
    """Manifesto JSON para auditoria determinística."""
    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "seed": seed,
        "permutations": permutations,
        "config": str(config_path),
        "inputs": {str(p): _file_sha256(p) for p in inputs if p.exists()},
        "outputs": [str(p) for p in outputs],
    }
    path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
