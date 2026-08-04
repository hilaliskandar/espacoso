from __future__ import annotations

"""Cartografia comparativa entre esquemas territoriais."""

from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np

matplotlib.use("Agg")

import geopandas as gpd  # noqa: E402


def _classify_quantiles(values, n_classes: int) -> tuple[np.ndarray, list[float]]:
    """Classifica valores em quantis, retornando rótulos (0-based) e limites."""
    quantiles = np.linspace(0, 100, n_classes + 1)
    breaks = np.nanpercentile(values, quantiles)
    # evitar divisões duplicadas
    breaks = np.unique(breaks)
    labels = np.digitize(values, breaks[1:-1], right=True)
    return labels, list(breaks)


def choropleth_map(
    gdf: gpd.GeoDataFrame,
    column: str,
    output_path: Path,
    title: str,
    n_classes: int = 5,
    cmap: str = "YlOrRd",
    breaks: list[float] | None = None,
) -> list[float]:
    """Cria mapa coroplético e salva em *output_path*.

    Retorna os limites de classe utilizados (para comparação entre mapas).
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    values = gdf[column].to_numpy(dtype=float)

    if breaks is None:
        _, used_breaks = _classify_quantiles(values, n_classes)
    else:
        used_breaks = breaks

    fig, ax = plt.subplots(figsize=(7, 6))
    gdf.plot(
        column=column,
        ax=ax,
        cmap=cmap,
        legend=True,
        scheme="user_defined",
        classification_kwds={"bins": used_breaks[1:-1]},
        edgecolor="white",
        linewidth=0.3,
        legend_kwds={"fmt": "{:.2f}", "loc": "lower right"},
        missing_kwds={"color": "lightgrey", "label": "sem dados"},
    )
    ax.set_title(title, fontsize=11)
    ax.axis("off")
    fig.tight_layout()
    fig.savefig(output_path, dpi=120, bbox_inches="tight")
    plt.close(fig)
    return used_breaks


def comparison_figure(
    frames: dict[str, gpd.GeoDataFrame],
    column_template: str,
    output_path: Path,
    title: str,
    n_classes: int = 5,
    cmap: str = "YlOrRd",
) -> None:
    """Figura lado a lado com mapas de cada esquema, usando classes compatíveis."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    n = len(frames)
    # determine global breaks
    all_values: list[float] = []
    for gdf in frames.values():
        if column_template in gdf.columns:
            all_values.extend(gdf[column_template].dropna().tolist())
    _, global_breaks = _classify_quantiles(np.asarray(all_values), n_classes)

    fig, axes = plt.subplots(1, n, figsize=(5 * n, 5))
    if n == 1:
        axes = [axes]

    for ax, (name, gdf) in zip(axes, frames.items()):
        if column_template not in gdf.columns:
            ax.set_visible(False)
            continue
        try:
            gdf.plot(
                column=column_template,
                ax=ax,
                cmap=cmap,
                legend=False,
                scheme="user_defined",
                classification_kwds={"bins": global_breaks[1:-1]},
                edgecolor="white",
                linewidth=0.3,
                missing_kwds={"color": "lightgrey"},
            )
        except Exception:
            gdf.plot(column=column_template, ax=ax, cmap=cmap, legend=False)
        ax.set_title(name, fontsize=10)
        ax.axis("off")

    fig.suptitle(title, fontsize=12, y=1.01)
    fig.tight_layout()
    fig.savefig(output_path, dpi=120, bbox_inches="tight")
    plt.close(fig)
