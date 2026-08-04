"""Pipeline principal de redes, acessibilidade e fluxos territoriais."""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import geopandas as gpd

from .accessibility import (
    compute_accessibility,
    compare_network_vs_euclidean,
)
from .cartography import (
    plot_accessibility_choropleth,
    plot_detour_map,
    plot_inequality_comparison,
    plot_network,
)
from .config import AppConfig, load_config
from .io import prepare_network, prepare_origins, read_spatial
from .network import (
    betweenness_centrality,
    closeness_centrality,
    degree_centrality,
    compute_all_pairs_shortest_paths,
    snap_origins_to_network,
)
from .reporting import build_inequality_table, build_manifest, write_json
from .topology import build_adjacency, build_node_index, validate_topology


def run_pipeline(config_path_or_obj: str | Path | AppConfig) -> dict:
    """
    Executa o pipeline completo de redes e acessibilidade.

    Aceita caminho para arquivo YAML ou objeto AppConfig (para testes).
    """
    if isinstance(config_path_or_obj, AppConfig):
        cfg = config_path_or_obj
        # For AppConfig objects passed directly, derive a config_path from output_dir
        config_path = cfg.output_dir / "config_inline.yml"
    else:
        config_path = Path(config_path_or_obj).resolve()
        cfg = load_config(config_path)

    output_dir = cfg.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------ #
    # 1. Leitura e preparação dos dados
    # ------------------------------------------------------------------ #
    network_raw = read_spatial(cfg.network_path, cfg.network_layer)
    network = prepare_network(network_raw, cfg.analysis_crs)

    origins_raw = read_spatial(cfg.origins_path, cfg.origins_layer)
    origins = prepare_origins(
        origins_raw,
        cfg.origins_id_column,
        cfg.opportunities_column,
        cfg.population_column,
        cfg.analysis_crs,
    )

    # ------------------------------------------------------------------ #
    # 2. Validação topológica
    # ------------------------------------------------------------------ #
    topology_report = validate_topology(network)

    # ------------------------------------------------------------------ #
    # 3. Construção da rede
    # ------------------------------------------------------------------ #
    node_map = build_node_index(network)
    adj = build_adjacency(network, node_map, directed=False)

    # Atribui origens aos nós da rede
    origin_nodes = snap_origins_to_network(origins, network, node_map)

    # Nós únicos de origem
    unique_origin_nodes = list(set(origin_nodes.values()))

    # Caminhos mínimos entre nós de origem
    all_distances = compute_all_pairs_shortest_paths(adj, unique_origin_nodes, cfg.max_cost)
    # Also compute from each origin node to all nodes (for full accessibility)
    all_distances_full = {n: {} for n in unique_origin_nodes}
    from .network import dijkstra
    for n in unique_origin_nodes:
        all_distances_full[n] = dijkstra(adj, n, cfg.max_cost)

    # ------------------------------------------------------------------ #
    # 4. Centralidade
    # ------------------------------------------------------------------ #
    centrality_results: dict[str, dict[int, float]] = {}
    if "betweenness" in cfg.centrality_measures:
        centrality_results["betweenness"] = betweenness_centrality(adj)
    if "closeness" in cfg.centrality_measures:
        centrality_results["closeness"] = closeness_centrality(adj)
    if "degree" in cfg.centrality_measures:
        centrality_results["degree"] = degree_centrality(adj)

    # ------------------------------------------------------------------ #
    # 5. Acessibilidade por função de impedância
    # ------------------------------------------------------------------ #
    # Build destinations DataFrame (origens também são destinos)
    origins_reset = origins.copy().reset_index()
    origins_reset["_node_id"] = origins_reset.index.map(
        lambda i: origin_nodes.get(origins_reset.index[i])
    )
    # Map origin index to node id for destinations
    dest_data = pd.DataFrame([
        {
            "_node_id": origin_nodes[idx],
            cfg.opportunities_column: float(origins.loc[idx, cfg.opportunities_column]),
        }
        for idx in origins.index
        if idx in origin_nodes
    ])

    accessibility_cols: list[str] = []
    for spec in cfg.impedances:
        col = f"acess_{spec.name}"
        acc = compute_accessibility(
            origin_nodes=origin_nodes,
            destinations=dest_data,
            destination_node_col="_node_id",
            opportunities_col=cfg.opportunities_column,
            all_distances=all_distances_full,
            spec=spec,
        )
        origins[col] = acc
        accessibility_cols.append(col)

    # ------------------------------------------------------------------ #
    # 6. Comparação rede vs euclidiana
    # ------------------------------------------------------------------ #
    detour_df = compare_network_vs_euclidean(
        origins, cfg.origins_id_column, origin_nodes, all_distances_full
    )

    # ------------------------------------------------------------------ #
    # 7. Tabela de desigualdades
    # ------------------------------------------------------------------ #
    inequality_table = build_inequality_table(
        origins, cfg.origins_id_column, accessibility_cols, cfg.population_column
    )

    # ------------------------------------------------------------------ #
    # 8. Saídas tabulares
    # ------------------------------------------------------------------ #
    outputs: list[Path] = []

    origins_out = output_dir / "origens_acessibilidade.gpkg"
    origins.to_file(origins_out, driver="GPKG")
    outputs.append(origins_out)

    topology_path = output_dir / "relatorio_topologia.json"
    write_json(topology_report.to_dict(), topology_path)
    outputs.append(topology_path)

    detour_path = output_dir / "comparacao_rede_euclidiana.csv"
    detour_df.to_csv(detour_path, index=False)
    outputs.append(detour_path)

    inequality_path = output_dir / "tabela_desigualdades.csv"
    inequality_table.to_csv(inequality_path, index=False)
    outputs.append(inequality_path)

    if centrality_results:
        cent_df = pd.DataFrame(centrality_results)
        cent_df.index.name = "node_id"
        cent_path = output_dir / "centralidade_nos.csv"
        cent_df.to_csv(cent_path)
        outputs.append(cent_path)

    # Paths mínimos entre origens
    paths_rows = []
    origin_ids = list(origins.index)
    for i, a in enumerate(origin_ids):
        for b in origin_ids[i + 1:]:
            node_a = origin_nodes.get(a)
            node_b = origin_nodes.get(b)
            cost = all_distances_full.get(node_a, {}).get(node_b, None)
            paths_rows.append({
                "origin_a": origins.loc[a, cfg.origins_id_column],
                "origin_b": origins.loc[b, cfg.origins_id_column],
                "network_cost_m": round(cost, 2) if cost is not None and cost < float("inf") else None,
            })
    paths_df = pd.DataFrame(paths_rows)
    paths_path = output_dir / "caminhos_minimos_origens.csv"
    paths_df.to_csv(paths_path, index=False)
    outputs.append(paths_path)

    # ------------------------------------------------------------------ #
    # 9. Mapas
    # ------------------------------------------------------------------ #
    if cfg.maps:
        net_map = output_dir / "mapa_rede.png"
        plot_network(network, origins, net_map, title="Rede viária e unidades territoriais")
        outputs.append(net_map)

        for col in accessibility_cols:
            acess_map = output_dir / f"mapa_{col}.png"
            plot_accessibility_choropleth(
                origins, col, acess_map,
                title=f"Acessibilidade — {col}",
            )
            outputs.append(acess_map)

        if accessibility_cols:
            comp_map = output_dir / "comparacao_impedancias.png"
            plot_inequality_comparison(origins, accessibility_cols, comp_map)
            outputs.append(comp_map)

        if not detour_df.empty:
            detour_map = output_dir / "mapa_desvio_rede.png"
            plot_detour_map(origins, cfg.origins_id_column, detour_df, detour_map)
            outputs.append(detour_map)

    # ------------------------------------------------------------------ #
    # 10. Relatório e manifesto
    # ------------------------------------------------------------------ #
    report = {
        "n_origins": len(origins),
        "origins_id_column": cfg.origins_id_column,
        "opportunities_column": cfg.opportunities_column,
        "population_column": cfg.population_column,
        "analysis_crs": cfg.analysis_crs,
        "topology": topology_report.to_dict(),
        "impedances": [
            {"name": s.name, "function": s.function, "cutoff": s.cutoff, "beta": s.beta}
            for s in cfg.impedances
        ],
        "inequality": inequality_table.to_dict(orient="records"),
        "context_note": (
            "A acessibilidade é calculada sobre uma rede sintética/simplificada. "
            "Sentidos de circulação, velocidades reais e impedâncias de travessia "
            "não são modelados nesta versão. Os resultados têm caráter didático."
        ),
    }
    report_path = output_dir / "relatorio_acessibilidade.json"
    write_json(report, report_path)
    outputs.append(report_path)

    manifest = build_manifest(config_path, cfg.network_path, cfg.origins_path, outputs)
    manifest_path = output_dir / "manifesto_execucao.json"
    write_json(manifest, manifest_path)
    outputs.append(manifest_path)

    return {
        "output_dir": str(output_dir),
        "outputs": [str(p) for p in outputs],
        "report": report,
    }
