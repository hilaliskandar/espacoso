from __future__ import annotations

from pathlib import Path

import pandas as pd

from .cartography import plot_getis_ord, plot_local_moran
from .config import AppConfig
from .io import read_spatial, validate_and_prepare
from .reporting import build_manifest, write_json
from .statistics import getis_ord_g_star, local_moran, permutation_global
from .weights import build_weights


def run_pipeline(config: AppConfig, config_path: Path) -> dict:
    output_dir = config.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    gdf = validate_and_prepare(
        read_spatial(config.input_path, config.input_layer),
        config.id_column,
        config.value_column,
        config.analysis_crs,
    )
    values = gdf[config.value_column].to_numpy(dtype=float)
    diagnostics_rows: list[dict] = []
    global_rows: list[dict] = []
    sensitivity_rows: list[dict] = []
    outputs: list[Path] = []
    primary_spatial = None

    for offset, spec in enumerate(config.weights):
        weights = build_weights(gdf, config.id_column, spec)
        diagnostics = weights.diagnostics()
        diagnostics_rows.append(diagnostics)
        edge_path = output_dir / f"pesos_{spec.name}.csv"
        weights.edge_list().to_csv(edge_path, index=False)
        outputs.append(edge_path)

        moran = permutation_global(values, weights, "moran", config.permutations, config.seed + offset * 10, config.alternative)
        geary = permutation_global(values, weights, "geary", config.permutations, config.seed + offset * 10 + 1, config.alternative)
        for statistic_name, result in (("Moran I", moran), ("Geary C", geary)):
            global_rows.append(
                {
                    "weights": spec.name,
                    "statistic": statistic_name,
                    "value": result.statistic,
                    "expected": result.expected,
                    "p_value": result.p_value,
                    "permutations": result.permutations,
                    "alternative": result.alternative,
                    "simulated_mean": result.simulated_mean,
                    "simulated_std": result.simulated_std,
                }
            )

        local = local_moran(values, weights, config.permutations, config.seed + offset * 10 + 2, config.alpha, config.fdr)
        gstar = getis_ord_g_star(values, weights, config.permutations, config.seed + offset * 10 + 3, config.alpha, config.fdr)
        local_path = output_dir / f"moran_local_{spec.name}.csv"
        gstar_path = output_dir / f"getis_ord_gstar_{spec.name}.csv"
        local.to_csv(local_path, index=False)
        gstar.to_csv(gstar_path, index=False)
        outputs.extend([local_path, gstar_path])

        sensitivity_rows.append(
            {
                **diagnostics,
                "moran_i": moran.statistic,
                "moran_p": moran.p_value,
                "geary_c": geary.statistic,
                "geary_p": geary.p_value,
                "local_moran_significant": int(local["significant"].sum()),
                "gstar_significant": int(gstar["significant"].sum()),
            }
        )

        if config.maps:
            moran_map = output_dir / f"mapa_moran_local_{spec.name}.png"
            gstar_map = output_dir / f"mapa_getis_ord_{spec.name}.png"
            plot_local_moran(gdf, local, config.id_column, moran_map, f"Moran local — {spec.name}")
            plot_getis_ord(gdf, gstar, config.id_column, gstar_map, f"Getis-Ord G* — {spec.name}")
            outputs.extend([moran_map, gstar_map])

        if spec.name == config.primary_weight:
            primary_spatial = gdf.merge(local.add_prefix("moran_"), left_on=config.id_column, right_on="moran_id", validate="one_to_one")
            primary_spatial = primary_spatial.merge(gstar.add_prefix("gstar_"), left_on=config.id_column, right_on="gstar_id", validate="one_to_one")

    diagnostics_path = output_dir / "diagnostico_matrizes.csv"
    global_path = output_dir / "estatisticas_globais.csv"
    sensitivity_path = output_dir / "sensibilidade_matrizes.csv"
    pd.DataFrame(diagnostics_rows).to_csv(diagnostics_path, index=False)
    pd.DataFrame(global_rows).to_csv(global_path, index=False)
    pd.DataFrame(sensitivity_rows).to_csv(sensitivity_path, index=False)
    outputs.extend([diagnostics_path, global_path, sensitivity_path])

    if primary_spatial is not None:
        primary_path = output_dir / "resultados_matriz_principal.gpkg"
        primary_spatial.to_file(primary_path, layer="resultados", driver="GPKG")
        outputs.append(primary_path)

    report = {
        "n_observations": len(gdf),
        "id_column": config.id_column,
        "value_column": config.value_column,
        "analysis_crs": str(gdf.crs),
        "primary_weight": config.primary_weight,
        "permutations": config.permutations,
        "seed": config.seed,
        "alpha": config.alpha,
        "fdr": config.fdr,
        "matrices": diagnostics_rows,
        "multiple_testing_note": "p-valores locais são acompanhados por q-valores de Benjamini-Hochberg; a classificação usa q quando fdr=true.",
    }
    report_path = output_dir / "relatorio_autocorrelacao.json"
    write_json(report, report_path)
    outputs.append(report_path)

    manifest_path = output_dir / "manifesto_execucao.json"
    manifest = build_manifest(config_path, config.input_path, outputs, config.seed, config.permutations)
    write_json(manifest, manifest_path)
    outputs.append(manifest_path)
    return {"output_dir": str(output_dir), "outputs": [str(path) for path in outputs], "report": report}
