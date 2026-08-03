from __future__ import annotations

import argparse
import hashlib
import json
import logging
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import sklearn
import yaml

from .data import load_dataset
from .features import CovariateLagTransformer, SpatialEigenvectorTransformer
from .metrics import (
    conformal_quantile,
    interval_metrics,
    local_moran,
    moran_i,
    regression_metrics,
)
from .models import append_features, build_model, parameter_grid
from .reporting import generate_maps, gate_decisions, optimism_table, write_gates
from .spatial_cv import ValidationDesign, build_splits, groups_for_design


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _load_config(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _prepare_features(frame: pd.DataFrame, target: str, coord_cols: list[str]):
    y = frame[target].to_numpy(dtype=float)
    coords = frame[coord_cols].to_numpy(dtype=float)
    feature_cols = [c for c in frame.columns if c != target and c not in coord_cols]
    x = frame[feature_cols].to_numpy(dtype=float)
    return x, y, coords, feature_cols


def _feature_matrices(
    model_id: str,
    x_train: np.ndarray,
    x_test: np.ndarray,
    c_train: np.ndarray,
    c_test: np.ndarray,
    cfg: dict,
):
    extra_train = extra_test = None
    if model_id in {"M2U", "M2D"}:
        lag_cfg = cfg["models"]["lag_features"]
        weighting = "uniform" if model_id == "M2U" else "inverse_distance"
        lagger = CovariateLagTransformer(
            k_neighbors=int(lag_cfg["k_neighbors"]),
            weighting=weighting,
            distance_power=float(lag_cfg.get("distance_power", 1.0)),
        ).fit(c_train, x_train)
        extra_train = lagger.transform_train()
        extra_test = lagger.transform_test(c_test)
    elif model_id == "M3":
        basis_cfg = cfg["models"]["spatial_basis"]
        basis = SpatialEigenvectorTransformer(
            n_components=int(basis_cfg["n_components"]),
            gamma=float(basis_cfg["gamma"]),
        ).fit(c_train)
        extra_train = basis.transform(c_train)
        extra_test = basis.transform(c_test)
    return append_features(x_train, extra_train), append_features(x_test, extra_test)


def _fit_predict(
    model_id: str,
    params: dict,
    x_train: np.ndarray,
    y_train: np.ndarray,
    c_train: np.ndarray,
    x_test: np.ndarray,
    c_test: np.ndarray,
    cfg: dict,
    seed: int,
):
    train_matrix, test_matrix = _feature_matrices(
        model_id, x_train, x_test, c_train, c_test, cfg
    )
    model = build_model(
        model_id,
        params,
        seed=seed,
        n_jobs=int(cfg["models"]["random_forest"].get("n_jobs", -1)),
    )
    model.fit(train_matrix, y_train)
    return model.predict(test_matrix)


def _inner_design(outer_design: ValidationDesign, cfg: dict) -> ValidationDesign:
    n_inner = int(cfg["validation"]["inner_splits"])
    if outer_design.kind == "random":
        return ValidationDesign(name="inner_random", kind="random", n_splits=n_inner)
    return ValidationDesign(
        name=f"inner_{outer_design.name}",
        kind="spatial",
        n_splits=n_inner,
        n_rows=outer_design.n_rows,
        n_cols=outer_design.n_cols,
        buffer_distance=outer_design.buffer_distance,
    )


def _tune_model(
    model_id: str,
    x_train: np.ndarray,
    y_train: np.ndarray,
    c_train: np.ndarray,
    outer_design: ValidationDesign,
    cfg: dict,
    seed: int,
):
    candidates = parameter_grid(model_id, cfg["models"])
    inner_design = _inner_design(outer_design, cfg)
    inner_folds = list(build_splits(c_train, inner_design, seed))
    tuning_rows = []
    for candidate_id, params in enumerate(candidates, start=1):
        fold_scores = []
        for inner_fold, (tr, va) in enumerate(inner_folds, start=1):
            pred = _fit_predict(
                model_id,
                params,
                x_train[tr],
                y_train[tr],
                c_train[tr],
                x_train[va],
                c_train[va],
                cfg,
                seed + candidate_id * 100 + inner_fold,
            )
            score = regression_metrics(y_train[va], pred)["rmse"]
            fold_scores.append(score)
        tuning_rows.append(
            {
                "candidate_id": candidate_id,
                "params": params,
                "mean_inner_rmse": float(np.mean(fold_scores)),
                "median_inner_rmse": float(np.median(fold_scores)),
            }
        )
    best = min(tuning_rows, key=lambda row: row["mean_inner_rmse"])
    return best["params"], tuning_rows, inner_folds


def _calibration_residuals(
    model_id: str,
    params: dict,
    x_train: np.ndarray,
    y_train: np.ndarray,
    c_train: np.ndarray,
    inner_folds: list[tuple[np.ndarray, np.ndarray]],
    cfg: dict,
    seed: int,
) -> np.ndarray:
    residuals = []
    for inner_fold, (tr, va) in enumerate(inner_folds, start=1):
        pred = _fit_predict(
            model_id,
            params,
            x_train[tr],
            y_train[tr],
            c_train[tr],
            x_train[va],
            c_train[va],
            cfg,
            seed + 7000 + inner_fold,
        )
        residuals.extend(np.abs(y_train[va] - pred))
    return np.asarray(residuals, dtype=float)


def _parse_designs(cfg: dict) -> list[ValidationDesign]:
    designs = []
    for raw in cfg["validation"]["designs"]:
        designs.append(
            ValidationDesign(
                name=str(raw["name"]),
                kind=str(raw["kind"]),
                n_splits=int(raw["n_splits"]),
                n_rows=int(raw["n_rows"]) if raw.get("n_rows") is not None else None,
                n_cols=int(raw["n_cols"]) if raw.get("n_cols") is not None else None,
                buffer_distance=float(raw.get("buffer_distance", 0.0)),
            )
        )
    return designs


def run(config_path: Path) -> None:
    cfg = _load_config(config_path)
    seed = int(cfg["experiment"]["seed"])
    np.random.seed(seed)

    output_dir = Path(cfg["experiment"]["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[logging.FileHandler(output_dir / "run.log"), logging.StreamHandler()],
        force=True,
    )

    dataset = load_dataset(
        dataset_name=str(cfg["data"]["dataset"]),
        sample_limit=cfg["data"].get("sample_limit"),
        seed=seed,
        path=cfg["data"].get("path"),
        target_column=cfg["data"].get("target", "MedHouseVal"),
        coordinate_columns=cfg["data"].get("coordinate_columns", ["Longitude", "Latitude"]),
    )
    frame = dataset.frame
    coord_cols = list(dataset.coordinate_columns)
    x, y, coords, feature_cols = _prepare_features(frame, dataset.target_column, coord_cols)

    designs = _parse_designs(cfg)
    models = list(cfg["models"]["enabled"])
    coverage_target = float(cfg["intervals"]["coverage"])
    moran_cfg = cfg["diagnostics"]["moran"]
    lisa_cfg = cfg["diagnostics"]["lisa"]

    metric_rows: list[dict] = []
    prediction_rows: list[dict] = []
    tuning_rows_all: list[dict] = []
    local_rows: list[dict] = []

    repetitions = int(cfg["validation"].get("repetitions", 1))
    repetition_start = int(cfg["validation"].get("repetition_start", 1))
    for repetition in range(repetition_start, repetition_start + repetitions):
        for design_id, design in enumerate(designs, start=1):
            groups = groups_for_design(coords, design)
            folds = list(build_splits(coords, design, seed + repetition * 1000 + design_id))
            for fold_id, (train_idx, test_idx) in enumerate(folds, start=1):
                for model_pos, model_id in enumerate(models, start=1):
                    fold_seed = (
                        seed
                        + repetition * 100000
                        + design_id * 10000
                        + fold_id * 100
                        + model_pos
                    )
                    logging.info(
                        "validation=%s fold=%s model=%s train=%s test=%s",
                        design.name,
                        fold_id,
                        model_id,
                        len(train_idx),
                        len(test_idx),
                    )
                    x_train, x_test = x[train_idx], x[test_idx]
                    y_train, y_test = y[train_idx], y[test_idx]
                    c_train, c_test = coords[train_idx], coords[test_idx]

                    best_params, tuning_rows, inner_folds = _tune_model(
                        model_id,
                        x_train,
                        y_train,
                        c_train,
                        design,
                        cfg,
                        fold_seed,
                    )
                    for row in tuning_rows:
                        tuning_rows_all.append(
                            {
                                "validation": design.name,
                                "repetition": repetition,
                                "fold": fold_id,
                                "model": model_id,
                                "selected": row["params"] == best_params,
                                "params_json": json.dumps(row["params"], sort_keys=True),
                                "mean_inner_rmse": row["mean_inner_rmse"],
                                "median_inner_rmse": row["median_inner_rmse"],
                            }
                        )

                    calibration = _calibration_residuals(
                        model_id,
                        best_params,
                        x_train,
                        y_train,
                        c_train,
                        inner_folds,
                        cfg,
                        fold_seed,
                    )
                    q = conformal_quantile(calibration, coverage_target)
                    pred = _fit_predict(
                        model_id,
                        best_params,
                        x_train,
                        y_train,
                        c_train,
                        x_test,
                        c_test,
                        cfg,
                        fold_seed + 9000,
                    )
                    lower = pred - q
                    upper = pred + q
                    residuals = y_test - pred
                    metrics = regression_metrics(y_test, pred)
                    metrics.update(interval_metrics(y_test, lower, upper))

                    for weighting in ["uniform", "inverse_distance"]:
                        mi, p_value = moran_i(
                            residuals,
                            c_test,
                            k=int(moran_cfg["k"]),
                            weighting=weighting,
                            permutations=int(moran_cfg["permutations"]),
                            seed=fold_seed,
                        )
                        suffix = "uniform" if weighting == "uniform" else "inverse_distance"
                        metrics[f"moran_i_{suffix}"] = mi
                        metrics[f"moran_p_{suffix}"] = p_value

                    metric_rows.append(
                        {
                            "validation": design.name,
                            "repetition": repetition,
                            "validation_kind": design.kind,
                            "fold": fold_id,
                            "model": model_id,
                            "n_train": len(train_idx),
                            "n_test": len(test_idx),
                            "buffer_distance": design.buffer_distance,
                            "best_params_json": json.dumps(best_params, sort_keys=True),
                            "conformal_q": q,
                            **metrics,
                        }
                    )

                    lisa = local_moran(
                        residuals,
                        c_test,
                        k=int(lisa_cfg["k"]),
                        weighting=str(lisa_cfg["weighting"]),
                        permutations=int(lisa_cfg["permutations"]),
                        seed=fold_seed,
                        alpha=float(lisa_cfg["alpha"]),
                    )
                    for pos, row_idx in enumerate(test_idx):
                        common = {
                            "row_id": int(row_idx),
                            "validation": design.name,
                            "repetition": repetition,
                            "fold": fold_id,
                            "model": model_id,
                            "longitude": float(coords[row_idx, 0]),
                            "latitude": float(coords[row_idx, 1]),
                            "spatial_group": int(groups[row_idx]),
                        }
                        prediction_rows.append(
                            {
                                **common,
                                "y_true": float(y[row_idx]),
                                "y_pred": float(pred[pos]),
                                "lower": float(lower[pos]),
                                "upper": float(upper[pos]),
                                "covered": bool(lower[pos] <= y[row_idx] <= upper[pos]),
                                "residual": float(residuals[pos]),
                                "absolute_error": float(abs(residuals[pos])),
                            }
                        )
                        local_rows.append(
                            {
                                **common,
                                "residual": float(residuals[pos]),
                                "local_i": float(lisa["local_i"][pos]),
                                "local_p": float(lisa["local_p"][pos]),
                                "spatial_lag": float(lisa["spatial_lag"][pos]),
                                "cluster": str(lisa["cluster"][pos]),
                            }
                        )

    metrics_df = pd.DataFrame(metric_rows)
    predictions_df = pd.DataFrame(prediction_rows)
    tuning_df = pd.DataFrame(tuning_rows_all)
    local_df = pd.DataFrame(local_rows)

    metrics_df.to_csv(output_dir / "metrics.csv", index=False)
    predictions_df.to_csv(output_dir / "predictions.csv", index=False)
    tuning_df.to_csv(output_dir / "hyperparameter_search.csv", index=False)
    local_df.to_csv(output_dir / "local_moran.csv", index=False)
    optimism_df = optimism_table(metrics_df)
    optimism_df.to_csv(output_dir / "optimism.csv", index=False)

    summary_columns = [
        "rmse",
        "mae",
        "r2",
        "interval_coverage",
        "interval_width",
        "moran_i_uniform",
        "moran_i_inverse_distance",
    ]
    summary = metrics_df.groupby(["validation", "model"])[summary_columns].agg(
        ["median", "mean", "std"]
    )
    summary.to_csv(output_dir / "summary.csv")

    gates = gate_decisions(metrics_df, local_df, coverage_target)
    write_gates(gates, output_dir / "gates.json")
    if bool(cfg["experiment"].get("generate_maps", True)):
        generate_maps(predictions_df, local_df, output_dir)

    (output_dir / "config_used.yml").write_text(
        config_path.read_text(encoding="utf-8"), encoding="utf-8"
    )
    config_bytes = config_path.read_bytes()
    data_path = Path(str(cfg["data"].get("path", "")))
    data_sha256 = _sha256_bytes(data_path.read_bytes()) if data_path.is_file() else None
    manifest = {
        "experiment": cfg["experiment"]["name"],
        "run_utc": datetime.now(timezone.utc).isoformat(),
        "python": sys.version,
        "platform": platform.platform(),
        "scikit_learn": sklearn.__version__,
        "n_observations": len(frame),
        "feature_columns": feature_cols,
        "coordinate_columns": coord_cols,
        "target": dataset.target_column,
        "models": models,
        "validation_designs": [design.__dict__ for design in designs],
        "seed": seed,
        "repetitions": repetitions,
        "repetition_start": repetition_start,
        "config_sha256": _sha256_bytes(config_bytes),
        "data_path": str(data_path) if str(data_path) else None,
        "data_sha256": data_sha256,
        "method_notes": {
            "M2U": "uniform kNN covariate lags use training observations only",
            "M2D": "inverse-distance kNN covariate lags use training observations only",
            "M3": "centered RBF spatial eigenbasis is fitted on training coordinates only",
            "intervals": "cross-validation residual quantile approximation; not an exact finite-sample CV+ implementation",
            "primary_validation": "all configured spatial designs",
        },
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    logging.info("completed; outputs written to %s", output_dir)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    args = parser.parse_args()
    run(args.config)


if __name__ == "__main__":
    main()
