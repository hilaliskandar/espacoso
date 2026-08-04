"""Cartografia para redes e acessibilidade."""
from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import pandas as pd
import numpy as np

matplotlib.use("Agg")


def plot_network(
    network: gpd.GeoDataFrame,
    origins: gpd.GeoDataFrame,
    output: Path,
    title: str = "Rede viária e origens",
) -> None:
    """Mapa da rede com as unidades de origem sobrepostas."""
    fig, ax = plt.subplots(figsize=(10, 8))
    network.plot(ax=ax, color="#888888", linewidth=0.8, zorder=1)
    origins.plot(ax=ax, color="steelblue", alpha=0.6, edgecolor="white", zorder=2)
    ax.set_title(title, fontsize=12)
    ax.set_axis_off()
    fig.tight_layout()
    fig.savefig(output, dpi=150)
    plt.close(fig)


def plot_accessibility_choropleth(
    gdf: gpd.GeoDataFrame,
    column: str,
    output: Path,
    title: str = "Acessibilidade",
    cmap: str = "YlOrRd",
    missing_color: str = "lightgray",
) -> None:
    """Mapa coroplético de acessibilidade."""
    fig, ax = plt.subplots(figsize=(10, 8))
    gdf.plot(
        column=column,
        ax=ax,
        cmap=cmap,
        legend=True,
        missing_kwds={"color": missing_color, "label": "Sem dados"},
        legend_kwds={"shrink": 0.7, "label": column},
    )
    ax.set_title(title, fontsize=12)
    ax.set_axis_off()
    fig.tight_layout()
    fig.savefig(output, dpi=150)
    plt.close(fig)


def plot_inequality_comparison(
    df: pd.DataFrame,
    impedance_columns: list[str],
    output: Path,
    title: str = "Comparação de acessibilidade por função de impedância",
) -> None:
    """Boxplot comparando distribuições de acessibilidade entre funções de impedância."""
    fig, ax = plt.subplots(figsize=(max(6, len(impedance_columns) * 2), 6))
    data = [df[col].dropna().values for col in impedance_columns]
    ax.boxplot(data, tick_labels=impedance_columns, patch_artist=True)
    ax.set_title(title, fontsize=12)
    ax.set_ylabel("Acessibilidade")
    ax.set_xlabel("Função de impedância")
    fig.tight_layout()
    fig.savefig(output, dpi=150)
    plt.close(fig)


def plot_detour_map(
    origins: gpd.GeoDataFrame,
    id_col: str,
    detour_df: pd.DataFrame,
    output: Path,
    title: str = "Razão de desvio médio (rede / euclidiana)",
    cmap: str = "RdYlGn_r",
) -> None:
    """
    Mapa do desvio médio por origem.

    detour_df deve ter colunas [origin, detour_ratio].
    """
    avg_detour = (
        detour_df.groupby("origin")["detour_ratio"]
        .mean()
        .reset_index()
        .rename(columns={"origin": id_col, "detour_ratio": "avg_detour"})
    )
    merged = origins.merge(avg_detour, on=id_col, how="left")
    fig, ax = plt.subplots(figsize=(10, 8))
    merged.plot(
        column="avg_detour",
        ax=ax,
        cmap=cmap,
        legend=True,
        missing_kwds={"color": "lightgray", "label": "Sem dados"},
        legend_kwds={"shrink": 0.7, "label": "Razão de desvio"},
    )
    ax.set_title(title, fontsize=12)
    ax.set_axis_off()
    fig.tight_layout()
    fig.savefig(output, dpi=150)
    plt.close(fig)
