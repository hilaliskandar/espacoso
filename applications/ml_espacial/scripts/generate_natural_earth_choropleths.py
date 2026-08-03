from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "natural_earth_real_v0_4"
RAW = ROOT / "data" / "raw" / "naturalearth_lowres" / "naturalearth_lowres.shp"
INDEX = ROOT / "data" / "processed" / "natural_earth_country_index_v0_4.csv"


def main() -> None:
    gdf = gpd.read_file(RAW)
    index = pd.read_csv(INDEX)
    gdf = gdf.merge(index[["row_id", "iso_a3"]], on="iso_a3", how="inner")
    predictions = pd.read_csv(OUT / "predictions.csv")
    local = pd.read_csv(OUT / "local_moran.csv")
    maps = OUT / "maps_choropleth"
    maps.mkdir(exist_ok=True)

    for validation in ["spatial_fine", "spatial_coarse_buffered"]:
        for model in ["M0", "M1", "M2U", "M3"]:
            p = predictions[(predictions.validation == validation) & (predictions.model == model)]
            residual = p.groupby("row_id", as_index=False)["residual"].mean()
            layer = gdf.merge(residual, on="row_id", how="left")
            vmax = float(layer["residual"].abs().quantile(0.98))
            fig, ax = plt.subplots(figsize=(12, 6))
            layer.plot(
                column="residual",
                cmap="coolwarm",
                vmin=-vmax,
                vmax=vmax,
                legend=True,
                missing_kwds={"color": "lightgrey"},
                ax=ax,
            )
            ax.set_axis_off()
            ax.set_title(f"Resíduo médio fora da amostra — {validation} — {model}")
            fig.tight_layout()
            fig.savefig(maps / f"residual_{validation}_{model}.png", dpi=180)
            plt.close(fig)

            loc = local[(local.validation == validation) & (local.model == model)].copy()
            loc["significant"] = loc["cluster"].ne("NS")
            share = loc.groupby("row_id", as_index=False)["significant"].mean()
            layer_lisa = gdf.merge(share, on="row_id", how="left")
            fig, ax = plt.subplots(figsize=(12, 6))
            layer_lisa.plot(
                column="significant",
                cmap="viridis",
                vmin=0,
                vmax=1,
                legend=True,
                missing_kwds={"color": "lightgrey"},
                ax=ax,
            )
            ax.set_axis_off()
            ax.set_title(f"Frequência de LISA significativo — {validation} — {model}")
            fig.tight_layout()
            fig.savefig(maps / f"lisa_share_{validation}_{model}.png", dpi=180)
            plt.close(fig)

    metrics = pd.read_csv(OUT / "metrics.csv")
    med = metrics.groupby(["validation", "model"], as_index=False)["rmse"].median()
    pivot = med.pivot(index="model", columns="validation", values="rmse")
    ax = pivot.plot(kind="bar", figsize=(10, 5))
    ax.set_ylabel("RMSE mediano")
    ax.set_xlabel("Modelo")
    ax.set_title("Desempenho por desenho de validação — benchmark territorial real")
    ax.legend(title="Validação")
    fig = ax.get_figure()
    fig.tight_layout()
    fig.savefig(maps / "rmse_by_validation.png", dpi=180)
    plt.close(fig)


if __name__ == "__main__":
    main()
