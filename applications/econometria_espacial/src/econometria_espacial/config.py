"""Configuração YAML para a aplicação econometria_espacial."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from .errors import ConfigError

_SPATIAL_MODELS = {"SAR", "SEM", "SLX", "SDM", "OLS"}
_TRANSFORMATIONS = {"binary", "row_standardized"}
_IMPACTS = {"sar", "sdm"}


@dataclass(frozen=True)
class WeightSpec:
    name: str
    path: Path
    origin_column: str = "origin_id"
    destination_column: str = "destination_id"
    weight_column: str = "weight"
    transformation: str = "row_standardized"


@dataclass(frozen=True)
class SpatialModelSpec:
    name: str
    model_type: str          # OLS | SAR | SEM | SLX | SDM
    target: str
    predictors: tuple[str, ...]
    weights_name: str        # referência ao WeightSpec
    add_constant: bool = True
    # para SLX e SDM: lags das covariadas
    lag_predictors: tuple[str, ...] = field(default_factory=tuple)  # type: ignore[assignment]
    # tolerância e máximo de iterações para ML
    tol: float = 1e-8
    max_iter: int = 1000


@dataclass(frozen=True)
class AnalysisConfig:
    input_path: Path
    id_column: str
    geometry_layer: str | None
    models: tuple[SpatialModelSpec, ...]
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

    weight_items = _require(raw, "weights")
    if not isinstance(weight_items, list) or not weight_items:
        raise ConfigError("weights deve conter ao menos uma matriz.")
    weights: list[WeightSpec] = []
    for item in weight_items:
        if not isinstance(item, dict):
            raise ConfigError("Cada matriz deve ser um objeto.")
        transformation = str(item.get("transformation", "row_standardized"))
        if transformation not in _TRANSFORMATIONS:
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
    weight_names = [w.name for w in weights]
    if len(weight_names) != len(set(weight_names)):
        raise ConfigError("Nomes de matrizes devem ser únicos.")

    model_items = _require(raw, "models")
    if not isinstance(model_items, list) or not model_items:
        raise ConfigError("models deve conter ao menos uma especificação.")
    models: list[SpatialModelSpec] = []
    for item in model_items:
        if not isinstance(item, dict):
            raise ConfigError("Cada modelo deve ser um objeto.")
        predictors = item.get("predictors")
        if not isinstance(predictors, list) or not predictors:
            raise ConfigError("Cada modelo deve conter predictors não vazio.")
        model_type = str(item.get("model_type", "OLS")).upper()
        if model_type not in _SPATIAL_MODELS:
            raise ConfigError(f"Tipo de modelo não suportado: {model_type}")
        wname = str(item.get("weights_name", weight_names[0]))
        if wname not in weight_names:
            raise ConfigError(f"weights_name '{wname}' não encontrado nas matrizes declaradas.")
        lag_predictors = item.get("lag_predictors", [])
        if not isinstance(lag_predictors, list):
            raise ConfigError("lag_predictors deve ser uma lista.")
        models.append(
            SpatialModelSpec(
                name=str(_require(item, "name")),
                model_type=model_type,
                target=str(_require(item, "target")),
                predictors=tuple(str(x) for x in predictors),
                weights_name=wname,
                add_constant=bool(item.get("add_constant", True)),
                lag_predictors=tuple(str(x) for x in lag_predictors),
                tol=float(item.get("tol", 1e-8)),
                max_iter=int(item.get("max_iter", 1000)),
            )
        )

    model_names = [m.name for m in models]
    if len(model_names) != len(set(model_names)):
        raise ConfigError("Nomes de modelos devem ser únicos.")

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
