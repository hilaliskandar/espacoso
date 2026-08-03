from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np


def residual_map(
    gdf: gpd.GeoDataFrame,
    residual_column: str,
    path: Path,
    title: str,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    values = gdf[residual_column].to_numpy(dtype=float)
    limit = float(np.nanmax(np.abs(values))) if len(values) else 1.0
    if not np.isfinite(limit) or limit == 0:
        limit = 1.0
    fig, ax = plt.subplots(figsize=(8, 7))
    gdf.plot(
        column=residual_column,
        cmap="RdBu_r",
        vmin=-limit,
        vmax=limit,
        linewidth=0.25,
        edgecolor="white",
        legend=True,
        ax=ax,
        missing_kwds={"color": "lightgrey", "label": "Sem dado"},
    )
    ax.set_title(title)
    ax.set_axis_off()
    fig.tight_layout()
    fig.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(fig)


def influence_map(
    gdf: gpd.GeoDataFrame,
    cooks_column: str,
    path: Path,
    title: str,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(8, 7))
    gdf.plot(
        column=cooks_column,
        cmap="OrRd",
        linewidth=0.25,
        edgecolor="white",
        legend=True,
        ax=ax,
        missing_kwds={"color": "lightgrey", "label": "Sem dado"},
    )
    ax.set_title(title)
    ax.set_axis_off()
    fig.tight_layout()
    fig.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(fig)
