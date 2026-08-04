from __future__ import annotations

"""Pipeline principal da análise MAUP."""

from pathlib import Path

import pandas as pd

from .aggregation import aggregate, verify_total_conservation
from .cartography import choropleth_map, comparison_figure
from .config import AnalysisConfig, load_config
from .io import read_geodata, write_geodata
from .reporting import write_manifest, write_report
from .statistics import (
    MoranResult,
    contiguity_matrix,
    descriptive_stats,
    permutation_moran,
    stability_table,
)


def run_pipeline(config_path: str | Path) -> list[Path]:
    config_path = Path(config_path).resolve()
    config: AnalysisConfig = load_config(config_path)
    output = config.output_dir
    output.mkdir(parents=True, exist_ok=True)

    base_gdf = read_geodata(config)
    outputs: list[Path] = []

    # ------------------------------------------------------------------
    # 1. Agregação por esquema
    # ------------------------------------------------------------------
    aggregated: dict[str, object] = {}  # scheme_name -> GeoDataFrame
    for scheme in config.schemes:
        agg = aggregate(base_gdf, scheme, config.variables)
        aggregated[scheme.name] = agg
        gpkg_path = output / f"agregado_{scheme.name}.gpkg"
        write_geodata(agg, gpkg_path, layer=scheme.name)
        outputs.append(gpkg_path)

    # ------------------------------------------------------------------
    # 2. Estatísticas descritivas
    # ------------------------------------------------------------------
    desc = descriptive_stats(aggregated, config.variables)
    desc_path = output / "estatisticas_descritivas.csv"
    desc.to_csv(desc_path, index=False)
    outputs.append(desc_path)

    # ------------------------------------------------------------------
    # 3. Autocorrelação espacial (Moran por esquema e variável)
    # ------------------------------------------------------------------
    moran_results: dict[str, dict[str, MoranResult]] = {}  # var -> scheme -> result
    for var in config.variables:
        moran_results[var] = {}
        for scheme_name, agg in aggregated.items():
            col = f"{var}_mean"
            if col not in agg.columns:
                continue
            vals = agg[col].to_numpy(dtype=float)
            if len(vals) < 3:
                continue
            w = contiguity_matrix(agg)
            seed = config.seed + hash(var + scheme_name) % 100_000
            try:
                result = permutation_moran(vals, w, config.permutations, seed)
            except Exception:
                continue
            moran_results[var][scheme_name] = result

    # ------------------------------------------------------------------
    # 4. Tabela de estabilidade
    # ------------------------------------------------------------------
    non_empty = {v: s for v, s in moran_results.items() if s}
    if non_empty:
        stab = stability_table(non_empty)
        stab_path = output / "estabilidade_moran.csv"
        stab.to_csv(stab_path, index=False)
        outputs.append(stab_path)
    else:
        stab = pd.DataFrame()

    # ------------------------------------------------------------------
    # 5. Conservação de totais
    # ------------------------------------------------------------------
    conservation: dict[str, dict[str, bool]] = {}
    for var in config.variables:
        conservation[var] = {}
        for scheme_name, agg in aggregated.items():
            result_map = verify_total_conservation(base_gdf, agg, (var,))
            conservation[var][scheme_name] = result_map[var]

    conserv_rows: list[dict] = []
    for var, by_scheme in conservation.items():
        for scheme, ok in by_scheme.items():
            conserv_rows.append({"variavel": var, "esquema": scheme, "conservado": ok})
    conserv_path = output / "conservacao_totais.csv"
    pd.DataFrame(conserv_rows).to_csv(conserv_path, index=False)
    outputs.append(conserv_path)

    # ------------------------------------------------------------------
    # 6. Cartografia
    # ------------------------------------------------------------------
    for var in config.variables:
        col = f"{var}_mean"
        # Figura comparativa entre esquemas
        frames_with_col = {k: v for k, v in aggregated.items() if col in v.columns}
        if len(frames_with_col) >= 2:
            fig_path = output / f"mapa_comparativo_{var}.png"
            comparison_figure(
                frames_with_col,
                col,
                fig_path,
                title=f"{var} — comparação entre esquemas",
                n_classes=config.classes,
                cmap=config.colormap,
            )
            outputs.append(fig_path)

        # Mapa individual por esquema
        for scheme_name, agg in aggregated.items():
            if col not in agg.columns:
                continue
            map_path = output / f"mapa_{scheme_name}_{var}.png"
            choropleth_map(
                agg,
                col,
                map_path,
                title=f"{var} — {scheme_name}",
                n_classes=config.classes,
                cmap=config.colormap,
            )
            outputs.append(map_path)

    # ------------------------------------------------------------------
    # 7. Relatório
    # ------------------------------------------------------------------
    report_path = output / "relatorio.md"
    write_report(report_path, desc, stab, conservation, non_empty, config.alpha)
    outputs.append(report_path)

    # ------------------------------------------------------------------
    # 8. Manifesto de auditoria
    # ------------------------------------------------------------------
    manifest_path = output / "manifesto.json"
    write_manifest(
        manifest_path,
        config_path=config_path,
        inputs=[config.input_path],
        outputs=outputs,
        seed=config.seed,
        permutations=config.permutations,
    )
    outputs.append(manifest_path)
    return outputs
