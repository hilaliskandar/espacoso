from __future__ import annotations

import json
import shutil
from pathlib import Path

import pandas as pd
import yaml

from src.reporting import generate_maps, gate_decisions, optimism_table, write_gates

ROOT = Path(__file__).resolve().parents[1]
INPUTS = [
    ROOT / "outputs" / "natural_earth_real_v0_4_rep1",
    ROOT / "outputs" / "natural_earth_real_v0_4_rep2",
]
OUT = ROOT / "outputs" / "natural_earth_real_v0_4"


def read_concat(name: str) -> pd.DataFrame:
    return pd.concat([pd.read_csv(folder / name) for folder in INPUTS], ignore_index=True)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    metrics = read_concat("metrics.csv")
    predictions = read_concat("predictions.csv")
    tuning = read_concat("hyperparameter_search.csv")
    local = read_concat("local_moran.csv")

    metrics.to_csv(OUT / "metrics.csv", index=False)
    predictions.to_csv(OUT / "predictions.csv", index=False)
    tuning.to_csv(OUT / "hyperparameter_search.csv", index=False)
    local.to_csv(OUT / "local_moran.csv", index=False)
    optimism_table(metrics).to_csv(OUT / "optimism.csv", index=False)

    summary_columns = [
        "rmse",
        "mae",
        "r2",
        "interval_coverage",
        "interval_width",
        "moran_i_uniform",
        "moran_i_inverse_distance",
    ]
    metrics.groupby(["validation", "model"])[summary_columns].agg(
        ["median", "mean", "std"]
    ).to_csv(OUT / "summary.csv")

    cfg = yaml.safe_load((ROOT / "config" / "experimento_natural_earth_v0_4.yml").read_text())
    gates = gate_decisions(metrics, local, float(cfg["intervals"]["coverage"]))
    write_gates(gates, OUT / "gates.json")
    generate_maps(predictions, local, OUT)

    manifests = [json.loads((folder / "manifest.json").read_text()) for folder in INPUTS]
    combined = {
        "experiment": "natural_earth_countries_real_v0_4",
        "component_runs": manifests,
        "n_observations": manifests[0]["n_observations"],
        "data_sha256": manifests[0]["data_sha256"],
        "repetitions": [1, 2],
        "models": manifests[0]["models"],
        "validation_designs": manifests[0]["validation_designs"],
        "feature_columns": manifests[0]["feature_columns"],
        "target": manifests[0]["target"],
    }
    (OUT / "manifest.json").write_text(json.dumps(combined, ensure_ascii=False, indent=2))
    shutil.copy2(ROOT / "config" / "experimento_natural_earth_v0_4.yml", OUT / "config_used.yml")
    (OUT / "run.log").write_text(
        "Merged independent repetitions 1 and 2.\n", encoding="utf-8"
    )
    print(f"merged outputs written to {OUT}")


if __name__ == "__main__":
    main()
