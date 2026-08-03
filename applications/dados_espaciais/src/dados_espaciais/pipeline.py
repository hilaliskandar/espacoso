from __future__ import annotations

from pathlib import Path

from .cartography import make_choropleth
from .config import load_config, resolve_path
from .io import load_spatial, load_table
from .reporting import make_manifest, spatial_metrics, write_json
from .validation import join_one_to_one, prepare_geometries, validate_numeric_columns


def run_pipeline(config_file: str | Path) -> dict[str, Path]:
    cfg, config_path = load_config(config_file)
    spatial_path = resolve_path(cfg["paths"]["spatial"], config_path)
    table_path = resolve_path(cfg["paths"]["table"], config_path)
    output_dir = resolve_path(cfg["paths"]["output_dir"], config_path)
    output_dir.mkdir(parents=True, exist_ok=True)

    spatial = load_spatial(spatial_path)
    table = load_table(table_path)
    numeric_columns = list(cfg.get("table", {}).get("numeric_columns", []))
    if cfg["map"]["column"] not in numeric_columns:
        numeric_columns.append(cfg["map"]["column"])
    validate_numeric_columns(table, numeric_columns)

    geometry_cfg = cfg.get("geometry", {})
    prepared, geometry_report = prepare_geometries(
        spatial,
        analysis_crs=cfg["crs"]["analysis"],
        repair_invalid=bool(geometry_cfg.get("repair_invalid", True)),
        allow_empty=bool(geometry_cfg.get("allow_empty", False)),
    )

    join_cfg = cfg.get("join", {})
    joined, join_report, unmatched, unused = join_one_to_one(
        prepared,
        table,
        spatial_key=cfg["keys"]["spatial"],
        table_key=cfg["keys"]["table"],
        minimum_match_rate=float(join_cfg.get("minimum_match_rate", 1.0)),
    )

    processed_path = output_dir / "territorios_processados.gpkg"
    quality_path = output_dir / "relatorio_qualidade.json"
    unmatched_path = output_dir / "chaves_espaciais_sem_correspondencia.csv"
    unused_path = output_dir / "chaves_tabulares_nao_utilizadas.csv"
    map_path = output_dir / cfg["map"]["output"]
    manifest_path = output_dir / "manifesto_execucao.json"

    joined.to_file(processed_path, driver="GPKG")
    unmatched.to_csv(unmatched_path, index=False)
    unused.to_csv(unused_path, index=False)

    map_cfg = cfg["map"]
    make_choropleth(
        joined,
        column=map_cfg["column"],
        output=map_path,
        title=map_cfg.get("title", map_cfg["column"]),
        method=map_cfg.get("scheme", "quantiles"),
        k=int(map_cfg.get("k", 5)),
        cmap=map_cfg.get("cmap", "viridis"),
        missing_color=map_cfg.get("missing_color", "lightgray"),
    )

    report = {
        "geometry": geometry_report.to_dict(),
        "join": join_report.to_dict(),
        "spatial_metrics": spatial_metrics(joined),
        "missing_values": {
            column: int(joined[column].isna().sum()) for column in numeric_columns
        },
    }
    write_json(report, quality_path)

    output_files = [processed_path, quality_path, unmatched_path, unused_path, map_path]
    manifest = make_manifest(
        config_path=config_path,
        spatial_path=spatial_path,
        table_path=table_path,
        output_files=output_files,
    )
    write_json(manifest, manifest_path)

    return {
        "processed": processed_path,
        "quality": quality_path,
        "unmatched": unmatched_path,
        "unused": unused_path,
        "map": map_path,
        "manifest": manifest_path,
    }
