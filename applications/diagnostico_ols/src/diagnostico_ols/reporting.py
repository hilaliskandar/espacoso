from __future__ import annotations

import hashlib
import json
import platform
from pathlib import Path
from typing import Iterable

import geopandas as gpd
import matplotlib
import numpy as np
import pandas as pd
import scipy
import statsmodels
import yaml


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_manifest(
    path: Path,
    config_path: Path,
    inputs: Iterable[Path],
    outputs: Iterable[Path],
    seed: int,
    permutations: int,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    input_list = [p for p in inputs if p.exists()]
    output_list = [p for p in outputs if p.exists() and p != path]
    payload = {
        "seed": seed,
        "permutations": permutations,
        "config": {"path": str(config_path), "sha256": sha256(config_path)},
        "inputs": [{"path": str(p), "sha256": sha256(p)} for p in input_list],
        "outputs": [{"path": str(p), "sha256": sha256(p)} for p in output_list],
        "versions": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "geopandas": gpd.__version__,
            "scipy": scipy.__version__,
            "statsmodels": statsmodels.__version__,
            "matplotlib": matplotlib.__version__,
            "pyyaml": yaml.__version__,
        },
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def write_report(
    path: Path,
    model_summary: pd.DataFrame,
    coefficients: pd.DataFrame,
    classical: pd.DataFrame,
    spatial: pd.DataFrame,
    vif: pd.DataFrame,
    alpha: float,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = [
        "# Relatório — OLS e diagnóstico espacial",
        "",
        "A aplicação compara especificações declaradas previamente. Os diagnósticos não selecionam automaticamente um modelo espacial e não demonstram causalidade.",
        "",
        "## Síntese dos modelos",
        "",
        model_summary.to_markdown(index=False, floatfmt=".4f"),
        "",
        "## Coeficientes",
        "",
        coefficients.to_markdown(index=False, floatfmt=".4f"),
        "",
        "## Diagnósticos clássicos",
        "",
        classical.to_markdown(index=False, floatfmt=".4f"),
        "",
        "## Multicolinearidade",
        "",
        vif.to_markdown(index=False, floatfmt=".4f") if not vif.empty else "Nenhum preditor para cálculo de VIF.",
        "",
        "## Diagnósticos espaciais por matriz",
        "",
        spatial.to_markdown(index=False, floatfmt=".4f"),
        "",
        "## Leitura orientada",
        "",
    ]
    for _, row in spatial.iterrows():
        moran_flag = "significativo" if row["moran_residual_p"] < alpha else "não significativo"
        lines.append(
            f"- **{row['model']} × {row['weights']}**: Moran residual {moran_flag} "
            f"(I={row['moran_residual']:.4f}; p={row['moran_residual_p']:.4f})."
        )
    lines.extend(
        [
            "",
            "## Limites",
            "",
            "- HC3 altera a inferência dos erros-padrão, não os coeficientes estimados.",
            "- VIF elevado sinaliza dependência linear entre regressoras, mas não define sozinho quais variáveis remover.",
            "- Moran residual e testes LM dependem da matriz de pesos e da especificação OLS.",
            "- Testes LM são diagnósticos condicionais; a escolha entre SAR, SEM, SLX ou SDM exige mecanismo substantivo e será tratada na A4.",
            "- Observações influentes devem ser investigadas, não removidas automaticamente.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
