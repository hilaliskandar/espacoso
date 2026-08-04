from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import matplotlib
import matplotlib.pyplot as plt
import numpy as np

matplotlib.use("Agg")


def _choropleth(
    gdf: gpd.GeoDataFrame,
    column: str,
    path: Path,
    title: str,
    cmap: str = "RdBu_r",
) -> None:
    fig, ax = plt.subplots(figsize=(8, 6))
    gdf.plot(column=column, ax=ax, cmap=cmap, legend=True, legend_kwds={"shrink": 0.7})
    ax.set_title(title, fontsize=12)
    ax.set_axis_off()
    fig.tight_layout()
    fig.savefig(path, dpi=120, bbox_inches="tight")
    plt.close(fig)


def residual_map(
    gdf: gpd.GeoDataFrame, column: str, path: Path, title: str
) -> None:
    _choropleth(gdf, column, path, title, cmap="RdBu_r")


def coefficient_surface(
    gdf: gpd.GeoDataFrame, column: str, path: Path, title: str
) -> None:
    _choropleth(gdf, column, path, title, cmap="coolwarm")


def local_r2_map(
    gdf: gpd.GeoDataFrame, column: str, path: Path, title: str
) -> None:
    _choropleth(gdf, column, path, title, cmap="YlOrRd")


def uncertainty_map(
    gdf: gpd.GeoDataFrame, column: str, path: Path, title: str
) -> None:
    _choropleth(gdf, column, path, title, cmap="Purples")


def comparison_barplot(
    comparison_df,
    metric: str,
    path: Path,
    title: str,
) -> None:
    fig, ax = plt.subplots(figsize=(7, 4))
    models = comparison_df["model"].tolist()
    values = comparison_df[metric].tolist()
    bars = ax.bar(models, values)
    ax.set_title(title, fontsize=12)
    ax.set_ylabel(metric)
    ax.set_xlabel("Modelo")
    for bar, val in zip(bars, values):
        if np.isfinite(val):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height(),
                f"{val:.3f}",
                ha="center",
                va="bottom",
                fontsize=9,
            )
    fig.tight_layout()
    fig.savefig(path, dpi=120, bbox_inches="tight")
    plt.close(fig)


def coefficient_boxplot(
    variability_df,
    path: Path,
    title: str,
) -> None:
    terms = variability_df["term"].tolist()
    means = variability_df["mean"].tolist()
    q25 = variability_df["q25"].tolist()
    q75 = variability_df["q75"].tolist()
    _min = variability_df["min"].tolist()
    _max = variability_df["max"].tolist()

    fig, ax = plt.subplots(figsize=(max(6, len(terms) * 1.5), 5))
    x = np.arange(len(terms))
    ax.bar(x, [h - l for h, l in zip(_max, _min)], bottom=_min, alpha=0.2, color="steelblue", label="min-max")
    ax.bar(x, [h - l for h, l in zip(q75, q25)], bottom=q25, alpha=0.6, color="steelblue", label="IQR")
    ax.plot(x, means, "o", color="navy", label="média")
    ax.set_xticks(x)
    ax.set_xticklabels(terms, rotation=30, ha="right")
    ax.set_title(title, fontsize=12)
    ax.set_ylabel("Coeficiente local")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=120, bbox_inches="tight")
    plt.close(fig)
