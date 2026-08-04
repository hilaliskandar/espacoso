"""Relatórios e manifesto de execução."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def write_json(obj: dict, path: Path) -> None:
    """Serializa dicionário para JSON com indentação."""
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False, default=str), encoding="utf-8")


def build_manifest(
    config_path: Path,
    network_path: Path,
    origins_path: Path,
    outputs: list[Path],
) -> dict:
    """Constrói manifesto de execução com hashes SHA-256."""
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "config": str(config_path),
        "inputs": {
            "network": {"path": str(network_path), "sha256": _sha256(network_path)},
            "origins": {"path": str(origins_path), "sha256": _sha256(origins_path)},
        },
        "outputs": [
            {"path": str(p), "sha256": _sha256(p)} for p in outputs if p.exists()
        ],
    }


def build_inequality_table(
    gdf: "gpd.GeoDataFrame",  # noqa: F821
    id_col: str,
    impedance_columns: list[str],
    population_col: str,
) -> pd.DataFrame:
    """
    Tabela de desigualdades territoriais de acessibilidade.

    Calcula percentis, razão entre máximo e mínimo, e coeficiente de variação.
    """
    rows = []
    for col in impedance_columns:
        series = gdf[col].dropna()
        pop = gdf.loc[series.index, population_col] if population_col in gdf.columns else None
        cv = series.std() / series.mean() if series.mean() != 0 else None
        row = {
            "impedance": col,
            "min": round(series.min(), 4),
            "p25": round(series.quantile(0.25), 4),
            "median": round(series.median(), 4),
            "p75": round(series.quantile(0.75), 4),
            "max": round(series.max(), 4),
            "mean": round(series.mean(), 4),
            "cv": round(cv, 4) if cv is not None else None,
            "max_min_ratio": round(series.max() / series.min(), 4) if series.min() > 0 else None,
            "n": len(series),
        }
        if pop is not None and pop.sum() > 0:
            weighted_mean = (series * pop).sum() / pop.sum()
            row["weighted_mean"] = round(float(weighted_mean), 4)
        rows.append(row)
    return pd.DataFrame(rows)
