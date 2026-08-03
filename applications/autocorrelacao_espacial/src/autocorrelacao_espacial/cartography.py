from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd


_MORAN_COLORS = {
    "HH": "#b2182b",
    "LL": "#2166ac",
    "HL": "#ef8a62",
    "LH": "#67a9cf",
    "NS": "#d9d9d9",
    "Island": "#636363",
}
_GSTAR_COLORS = {"Hot": "#b2182b", "Cold": "#2166ac", "NS": "#d9d9d9"}


def _merge(gdf: gpd.GeoDataFrame, table: pd.DataFrame, id_column: str) -> gpd.GeoDataFrame:
    left = gdf.copy()
    left[id_column] = left[id_column].astype(str)
    right = table.copy()
    right["id"] = right["id"].astype(str)
    return left.merge(right, left_on=id_column, right_on="id", how="left", validate="one_to_one")


def plot_local_moran(
    gdf: gpd.GeoDataFrame,
    table: pd.DataFrame,
    id_column: str,
    output: Path,
    title: str,
) -> None:
    merged = _merge(gdf, table, id_column)
    fig, ax = plt.subplots(figsize=(8, 7))
    merged.plot(color=merged["cluster"].map(_MORAN_COLORS), edgecolor="white", linewidth=0.6, ax=ax)
    handles = [plt.Line2D([0], [0], marker="s", linestyle="", markerfacecolor=color, markeredgecolor="none", markersize=10, label=label) for label, color in _MORAN_COLORS.items()]
    ax.legend(handles=handles, title="Moran local", loc="lower left", frameon=True)
    ax.set_title(title)
    ax.set_axis_off()
    fig.tight_layout()
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=180, bbox_inches="tight")
    plt.close(fig)


def plot_getis_ord(
    gdf: gpd.GeoDataFrame,
    table: pd.DataFrame,
    id_column: str,
    output: Path,
    title: str,
) -> None:
    merged = _merge(gdf, table, id_column)
    fig, ax = plt.subplots(figsize=(8, 7))
    merged.plot(color=merged["classification"].map(_GSTAR_COLORS), edgecolor="white", linewidth=0.6, ax=ax)
    handles = [plt.Line2D([0], [0], marker="s", linestyle="", markerfacecolor=color, markeredgecolor="none", markersize=10, label=label) for label, color in _GSTAR_COLORS.items()]
    ax.legend(handles=handles, title="Getis-Ord G*", loc="lower left", frameon=True)
    ax.set_title(title)
    ax.set_axis_off()
    fig.tight_layout()
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=180, bbox_inches="tight")
    plt.close(fig)
