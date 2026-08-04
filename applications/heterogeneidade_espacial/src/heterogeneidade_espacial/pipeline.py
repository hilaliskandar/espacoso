from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

from .cartography import (
    coefficient_boxplot,
    coefficient_surface,
    comparison_barplot,
    local_r2_map,
    residual_map,
    uncertainty_map,
)
from .config import AnalysisConfig, load_config
from .data import build_design, extract_coordinates, read_geodata, write_geodata
from .diagnostics import bootstrap_stability, coefficient_variability, comparison_table
from .global_model import fit_global, global_coefficient_table, global_summary, vif_table
from .gwr_model import (
    GWRResult,
    fit_gwr,
    fit_mgwr,
    gwr_coefficient_table,
    gwr_summary,
    local_collinearity,
    select_bandwidth,
)
from .reporting import write_manifest, write_report


def _attach_local(gdf: gpd.GeoDataFrame, res: GWRResult) -> gpd.GeoDataFrame:
    prefix = res.model_name.lower()
    gdf = gdf.copy()
    gdf[f"fitted_{prefix}"] = res.fitted
    gdf[f"residual_{prefix}"] = res.residuals
    gdf[f"localr2_{prefix}"] = res.localr2
    gdf[f"influence_{prefix}"] = res.influence
    for j, name in enumerate(res.feature_names):
        safe = name.replace(" ", "_")
        gdf[f"coef_{prefix}_{safe}"] = res.params[:, j]
        gdf[f"se_{prefix}_{safe}"] = res.std_errors[:, j]
        gdf[f"tval_{prefix}_{safe}"] = res.t_values[:, j]
    return gdf


def run_pipeline(config_path: str | Path) -> list[Path]:
    config_path = Path(config_path).resolve()
    config: AnalysisConfig = load_config(config_path)
    output = config.output_dir
    output.mkdir(parents=True, exist_ok=True)

    gdf = read_geodata(config)
    ids = gdf[config.id_column].astype(str).tolist()
    coords = extract_coordinates(gdf)
    y, x, feature_names = build_design(
        gdf, config.target, config.predictors, config.add_constant
    )

    outputs: list[Path] = []

    # ── Global OLS ──────────────────────────────────────────────────────────
    global_res = fit_global(y, x, feature_names, config.robust_covariance)
    global_coef = global_coefficient_table(global_res)
    global_summ = global_summary(global_res)
    vif = vif_table(x, feature_names)

    result_gdf = gdf.copy()
    result_gdf["fitted_ols"] = global_res.fitted
    result_gdf["residual_ols"] = global_res.residuals

    ols_residual_map = output / "mapa_residuos_ols.png"
    residual_map(result_gdf, "residual_ols", ols_residual_map, "Resíduos OLS global")
    outputs.append(ols_residual_map)

    # ── GWR ─────────────────────────────────────────────────────────────────
    gwr_bw = select_bandwidth(coords, y, x, config.bandwidth)
    gwr_res = fit_gwr(coords, y, x, feature_names, config.bandwidth, bandwidth=gwr_bw)
    result_gdf = _attach_local(result_gdf, gwr_res)

    gwr_coef = gwr_coefficient_table(gwr_res, ids)
    gwr_summ = gwr_summary(gwr_res)
    gwr_variab = coefficient_variability(gwr_res)
    gwr_coll = local_collinearity(gwr_res)

    gwr_residual_map = output / "mapa_residuos_gwr.png"
    residual_map(result_gdf, "residual_gwr", gwr_residual_map, "Resíduos GWR")
    outputs.append(gwr_residual_map)

    local_r2_path = output / "mapa_localr2_gwr.png"
    local_r2_map(result_gdf, "localr2_gwr", local_r2_path, "R² local — GWR")
    outputs.append(local_r2_path)

    for name in feature_names:
        safe = name.replace(" ", "_")
        col = f"coef_gwr_{safe}"
        se_col = f"se_gwr_{safe}"
        coef_path = output / f"mapa_coef_gwr_{safe}.png"
        coefficient_surface(result_gdf, col, coef_path, f"Coeficiente GWR — {name}")
        outputs.append(coef_path)
        unc_path = output / f"mapa_se_gwr_{safe}.png"
        uncertainty_map(result_gdf, se_col, unc_path, f"Erro padrão GWR — {name}")
        outputs.append(unc_path)

    gwr_boxplot_path = output / "boxplot_coef_gwr.png"
    coefficient_boxplot(gwr_variab, gwr_boxplot_path, "Variabilidade dos coeficientes — GWR")
    outputs.append(gwr_boxplot_path)

    # ── MGWR ────────────────────────────────────────────────────────────────
    mgwr_res: GWRResult | None = None
    mgwr_coef = pd.DataFrame()
    mgwr_summ: dict = {}
    mgwr_variab = pd.DataFrame()
    mgwr_coll = pd.DataFrame()

    if config.run_mgwr:
        mgwr_res = fit_mgwr(coords, y, x, feature_names, config.mgwr_bandwidth)
        result_gdf = _attach_local(result_gdf, mgwr_res)
        mgwr_coef = gwr_coefficient_table(mgwr_res, ids)
        mgwr_summ = gwr_summary(mgwr_res)
        mgwr_variab = coefficient_variability(mgwr_res)
        mgwr_coll = local_collinearity(mgwr_res)

        mgwr_residual_map = output / "mapa_residuos_mgwr.png"
        residual_map(result_gdf, "residual_mgwr", mgwr_residual_map, "Resíduos MGWR")
        outputs.append(mgwr_residual_map)

        for name in feature_names:
            safe = name.replace(" ", "_")
            coef_path = output / f"mapa_coef_mgwr_{safe}.png"
            coefficient_surface(
                result_gdf, f"coef_mgwr_{safe}", coef_path, f"Coeficiente MGWR — {name}"
            )
            outputs.append(coef_path)
            unc_path = output / f"mapa_se_mgwr_{safe}.png"
            uncertainty_map(
                result_gdf, f"se_mgwr_{safe}", unc_path, f"Erro padrão MGWR — {name}"
            )
            outputs.append(unc_path)

        mgwr_boxplot_path = output / "boxplot_coef_mgwr.png"
        coefficient_boxplot(mgwr_variab, mgwr_boxplot_path, "Variabilidade dos coeficientes — MGWR")
        outputs.append(mgwr_boxplot_path)

    # ── Bootstrap stability ─────────────────────────────────────────────────
    bootstrap_df = bootstrap_stability(
        coords=coords,
        y=y,
        x=x,
        feature_names=feature_names,
        bandwidth=gwr_bw,
        spec=config.bandwidth,
        n_bootstrap=config.n_bootstrap,
        fraction=config.bootstrap_fraction,
        seed=config.seed,
    )

    # ── Comparison ──────────────────────────────────────────────────────────
    local_models = [gwr_res]
    if mgwr_res is not None:
        local_models.append(mgwr_res)
    comparison = comparison_table(global_res, *local_models)

    comparison_bar_path = output / "comparacao_aic.png"
    comparison_barplot(comparison, "aic", comparison_bar_path, "AIC por modelo")
    outputs.append(comparison_bar_path)

    comparison_r2_path = output / "comparacao_r2.png"
    comparison_barplot(comparison, "r_squared", comparison_r2_path, "R² por modelo")
    outputs.append(comparison_r2_path)

    # ── Persist GeoPackage ──────────────────────────────────────────────────
    gpkg_path = output / "heterogeneidade_espacial.gpkg"
    write_geodata(result_gdf, gpkg_path, layer="resultado")
    outputs.append(gpkg_path)

    # ── CSV tables ──────────────────────────────────────────────────────────
    tables: dict[str, pd.DataFrame] = {
        "coeficientes_globais.csv": global_coef,
        "resumo_modelos.csv": pd.DataFrame(
            [global_summ, gwr_summ, *([] if not mgwr_summ else [mgwr_summ])]
        ),
        "vif_global.csv": vif,
        "coeficientes_gwr.csv": gwr_coef,
        "variabilidade_gwr.csv": gwr_variab,
        "colinearidade_local_gwr.csv": gwr_coll,
        "comparacao_modelos.csv": comparison,
    }
    if not mgwr_coef.empty:
        tables["coeficientes_mgwr.csv"] = mgwr_coef
        tables["variabilidade_mgwr.csv"] = mgwr_variab
        tables["colinearidade_local_mgwr.csv"] = mgwr_coll
    if not bootstrap_df.empty:
        tables["estabilidade_bootstrap.csv"] = bootstrap_df

    for filename, df in tables.items():
        p = output / filename
        df.to_csv(p, index=False)
        outputs.append(p)

    # ── Report ──────────────────────────────────────────────────────────────
    variab_frames = {"GWR": gwr_variab}
    if not mgwr_variab.empty:
        variab_frames["MGWR"] = mgwr_variab

    report_path = output / "relatorio.md"
    write_report(report_path, comparison.copy(), variab_frames, config.alpha)
    outputs.append(report_path)

    # ── Manifest ────────────────────────────────────────────────────────────
    manifest_path = output / "manifesto.json"
    write_manifest(
        manifest_path,
        config_path=config_path,
        inputs=[config.input_path],
        outputs=outputs,
        seed=config.seed,
    )
    outputs.append(manifest_path)

    return outputs
