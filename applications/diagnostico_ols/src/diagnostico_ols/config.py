from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from .errors import ConfigError


@dataclass(frozen=True)
class ModelSpec:
    name: str
    target: str
    predictors: tuple[str, ...]
    add_constant: bool = True
    robust_covariance: str = "HC3"


@dataclass(frozen=True)
class WeightSpec:
    name: str
    path: Path
    origin_column: str = "origin_id"
    destination_column: str = "destination_id"
    weight_column: str = "weight"
    transformation: str = "row_standardized"


@dataclass(frozen=True)
class AnalysisConfig:
    input_path: Path
    id_column: str
    geometry_layer: str | None
    models: tuple[ModelSpec, ...]
    weights: tuple[WeightSpec, ...]
    primary_model: str
    primary_weights: str
    permutations: int
    seed: int
    alpha: float
    output_dir: Path


def _resolve(base: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else (base / path).resolve()


def _require(mapping: dict[str, Any], key: str) -> Any:
    if key not in mapping:
        raise ConfigError(f"Campo obrigatório ausente: {key}")
    return mapping[key]


def load_config(path: str | Path) -> AnalysisConfig:
    config_path = Path(path).resolve()
    raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ConfigError("A configuração deve ser um objeto YAML.")

    base = config_path.parent
    data = _require(raw, "data")
    output = _require(raw, "output")
    if not isinstance(data, dict) or not isinstance(output, dict):
        raise ConfigError("data e output devem ser objetos.")

    model_items = _require(raw, "models")
    if not isinstance(model_items, list) or not model_items:
        raise ConfigError("models deve conter ao menos uma especificação.")
    models: list[ModelSpec] = []
    for item in model_items:
        if not isinstance(item, dict):
            raise ConfigError("Cada modelo deve ser um objeto.")
        predictors = item.get("predictors")
        if not isinstance(predictors, list) or not predictors:
            raise ConfigError("Cada modelo deve conter predictors não vazio.")
        robust = str(item.get("robust_covariance", "HC3")).upper()
        if robust not in {"HC0", "HC1", "HC2", "HC3"}:
            raise ConfigError(f"Covariância robusta não suportada: {robust}")
        models.append(
            ModelSpec(
                name=str(_require(item, "name")),
                target=str(_require(item, "target")),
                predictors=tuple(str(x) for x in predictors),
                add_constant=bool(item.get("add_constant", True)),
                robust_covariance=robust,
            )
        )

    weight_items = _require(raw, "weights")
    if not isinstance(weight_items, list) or not weight_items:
        raise ConfigError("weights deve conter ao menos uma matriz.")
    weights: list[WeightSpec] = []
    for item in weight_items:
        if not isinstance(item, dict):
            raise ConfigError("Cada matriz deve ser um objeto.")
        transformation = str(item.get("transformation", "row_standardized"))
        if transformation not in {"binary", "row_standardized"}:
            raise ConfigError(f"Transformação inválida: {transformation}")
        weights.append(
            WeightSpec(
                name=str(_require(item, "name")),
                path=_resolve(base, str(_require(item, "path"))),
                origin_column=str(item.get("origin_column", "origin_id")),
                destination_column=str(item.get("destination_column", "destination_id")),
                weight_column=str(item.get("weight_column", "weight")),
                transformation=transformation,
            )
        )

    model_names = [m.name for m in models]
    weight_names = [w.name for w in weights]
    if len(model_names) != len(set(model_names)):
        raise ConfigError("Nomes de modelos devem ser únicos.")
    if len(weight_names) != len(set(weight_names)):
        raise ConfigError("Nomes de matrizes devem ser únicos.")

    primary_model = str(_require(raw, "primary_model"))
    primary_weights = str(_require(raw, "primary_weights"))
    if primary_model not in model_names:
        raise ConfigError("primary_model não corresponde a um modelo declarado.")
    if primary_weights not in weight_names:
        raise ConfigError("primary_weights não corresponde a uma matriz declarada.")

    permutations = int(raw.get("permutations", 999))
    if permutations < 99:
        raise ConfigError("permutations deve ser >= 99.")
    alpha = float(raw.get("alpha", 0.05))
    if not 0 < alpha < 1:
        raise ConfigError("alpha deve estar entre 0 e 1.")

    return AnalysisConfig(
        input_path=_resolve(base, str(_require(data, "path"))),
        id_column=str(_require(data, "id_column")),
        geometry_layer=data.get("layer"),
        models=tuple(models),
        weights=tuple(weights),
        primary_model=primary_model,
        primary_weights=primary_weights,
        permutations=permutations,
        seed=int(raw.get("seed", 42)),
        alpha=alpha,
        output_dir=_resolve(base, str(_require(output, "dir"))),
    )
