from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd

from .errors import DataContractError


def classify(values: pd.Series, method: str, k: int) -> pd.Series:
    numeric = pd.to_numeric(values, errors="coerce")
    valid = numeric.dropna()
    result = pd.Series(pd.NA, index=values.index, dtype="object")
    if valid.empty:
        raise DataContractError("Não há valores válidos para a cartografia.")
    bins = min(max(1, int(k)), int(valid.nunique()))
    if bins <= 1:
        result.loc[valid.index] = "valor único"
        return result
    if method == "quantiles":
        classified = pd.qcut(valid, q=bins, duplicates="drop")
    elif method == "equal_interval":
        classified = pd.cut(valid, bins=bins, include_lowest=True)
    else:
        raise DataContractError(
            f"Método de classificação não suportado: {method}. "
            "Use quantiles ou equal_interval."
        )
    result.loc[valid.index] = classified.astype(str)
    return result


def make_choropleth(
    frame: gpd.GeoDataFrame,
    column: str,
    output: Path,
    title: str,
    method: str = "quantiles",
    k: int = 5,
    cmap: str = "viridis",
    missing_color: str = "lightgray",
) -> Path:
    if column not in frame.columns:
        raise DataContractError(f"Coluna cartográfica ausente: {column}")
    plot_frame = frame.copy()
    plot_frame["_map_class"] = classify(plot_frame[column], method=method, k=k)
    output.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(10, 8))
    plot_frame.plot(
        column="_map_class",
        categorical=True,
        legend=True,
        cmap=cmap,
        missing_kwds={"color": missing_color, "label": "Sem dado"},
        edgecolor="white",
        linewidth=0.6,
        ax=ax,
    )
    ax.set_title(title)
    ax.set_axis_off()
    fig.tight_layout()
    fig.savefig(output, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return output
