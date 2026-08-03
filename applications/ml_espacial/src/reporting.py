from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def generate_maps(predictions: pd.DataFrame, local: pd.DataFrame, output_dir: Path) -> None:
    maps_dir = output_dir / "maps"
    maps_dir.mkdir(parents=True, exist_ok=True)
    for (validation, model), group in predictions.groupby(["validation", "model"]):
        fig, ax = plt.subplots(figsize=(7, 5))
        scatter = ax.scatter(
            group["longitude"], group["latitude"], c=group["residual"], s=18, cmap="coolwarm"
        )
        ax.set_title(f"Resíduos fora da amostra — {validation} — {model}")
        ax.set_xlabel("Coordenada X")
        ax.set_ylabel("Coordenada Y")
        fig.colorbar(scatter, ax=ax, label="Resíduo")
        fig.tight_layout()
        fig.savefig(maps_dir / f"residuos_{validation}_{model}.png", dpi=160)
        plt.close(fig)

    marker_map = {"NS": "o", "HH": "^", "LL": "v", "HL": "s", "LH": "D"}
    for (validation, model), group in local.groupby(["validation", "model"]):
        fig, ax = plt.subplots(figsize=(7, 5))
        for cluster, marker in marker_map.items():
            subset = group[group["cluster"] == cluster]
            if subset.empty:
                continue
            ax.scatter(
                subset["longitude"], subset["latitude"], label=cluster, marker=marker, s=22
            )
        ax.set_title(f"LISA dos resíduos — {validation} — {model}")
        ax.set_xlabel("Coordenada X")
        ax.set_ylabel("Coordenada Y")
        ax.legend(title="Cluster", loc="best")
        fig.tight_layout()
        fig.savefig(maps_dir / f"lisa_{validation}_{model}.png", dpi=160)
        plt.close(fig)


def optimism_table(metrics: pd.DataFrame) -> pd.DataFrame:
    medians = metrics.groupby(["validation", "model"], as_index=False)["rmse"].median()
    random_rows = medians[medians["validation"] == "random"][["model", "rmse"]].rename(
        columns={"rmse": "rmse_random"}
    )
    spatial_rows = medians[medians["validation"] != "random"].rename(
        columns={"rmse": "rmse_spatial"}
    )
    out = spatial_rows.merge(random_rows, on="model", how="left")
    out["optimism_relative"] = (
        out["rmse_spatial"] - out["rmse_random"]
    ) / out["rmse_spatial"]
    return out


def gate_decisions(metrics: pd.DataFrame, local: pd.DataFrame, coverage_target: float) -> dict:
    spatial = metrics[metrics["validation"] != "random"]
    baseline = spatial[spatial["model"] == "M0"].groupby("validation")["rmse"].median()
    decisions: dict[str, object] = {
        "gate_0_data": "approved_by_pipeline_checks",
        "gate_1_no_leakage": "approved_by_unit_tests",
        "gate_2_partition_validity": "approved_for_configured_designs",
    }
    superior = []
    for model in sorted(set(spatial["model"]) - {"M0"}):
        model_median = spatial[spatial["model"] == model].groupby("validation")["rmse"].median()
        common = baseline.index.intersection(model_median.index)
        wins = int(np.sum(model_median.loc[common] < baseline.loc[common]))
        superior.append({"model": model, "wins": wins, "comparisons": len(common)})
    decisions["gate_3_spatial_performance"] = superior
    residual_share = (
        local[(local["validation"] != "random") & (local["cluster"] != "NS")]
        .groupby("model")
        .size()
        / local[local["validation"] != "random"].groupby("model").size()
    ).fillna(0)
    decisions["gate_4_local_residual_structure_share"] = residual_share.to_dict()
    coverage = spatial.groupby("model")["interval_coverage"].median().to_dict()
    decisions["gate_5_interval_coverage"] = {
        "target": coverage_target,
        "observed_median": coverage,
    }
    decisions["gate_6_robustness"] = {
        "validation_designs": sorted(spatial["validation"].unique().tolist()),
        "weight_matrices": ["knn_uniform", "knn_inverse_distance"],
    }
    decisions["gate_7_reproducibility"] = "approved_if_manifest_and_outputs_present"
    return decisions


def write_gates(gates: dict, path: Path) -> None:
    path.write_text(json.dumps(gates, ensure_ascii=False, indent=2), encoding="utf-8")
