from __future__ import annotations

"""Configuração do pipeline de painéis espaciais."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from .errors import PanelError
from .weights import WeightSpec


@dataclass(frozen=True)
class ModelSpec:
    """Especificação de um modelo de painel."""

    name: str
    target: str
    predictors: tuple[str, ...]
    fixed_effects: str = "unit"
    model_type: str = "fe"
    dynamic: bool = False
    n_lags: int = 1


@dataclass(frozen=True)
class PanelConfig:
    """Configuração completa da análise de painel."""

    input_path: Path
    unit_col: str
    time_col: str
    geometry_layer: str | None
    gap_strategy: str
    gap_limit: int
    models: tuple[ModelSpec, ...]
    weights: tuple[WeightSpec, ...]
    seed: int
    alpha: float
    output_dir: Path


def _resolve(base: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else (base / path).resolve()


def _require(mapping: dict[str, Any], key: str) -> Any:
    if key not in mapping:
        raise PanelError(f"Campo obrigatório ausente: {key}")
    return mapping[key]


def load_config(path: str | Path) -> PanelConfig:
    """Carrega configuração YAML para análise de painel espacial.

    Parameters
    ----------
    path:
        Caminho para o arquivo ``.yml``.

    Returns
    -------
    PanelConfig

    Raises
    ------
    PanelError
        Se a configuração for inválida ou incompleta.
    """
    config_path = Path(path).resolve()
    raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise PanelError("A configuração deve ser um objeto YAML.")

    base = config_path.parent
    data = _require(raw, "data")
    output = _require(raw, "output")
    if not isinstance(data, dict) or not isinstance(output, dict):
        raise PanelError("data e output devem ser objetos.")

    model_items = _require(raw, "models")
    if not isinstance(model_items, list) or not model_items:
        raise PanelError("models deve conter ao menos uma especificação.")

    valid_fe = {"unit", "time", "two_way"}
    valid_types = {"fe", "spatial_lag", "spatial_error"}
    valid_gaps = {"none", "forward_fill", "backward_fill", "interpolate"}

    models: list[ModelSpec] = []
    for item in model_items:
        if not isinstance(item, dict):
            raise PanelError("Cada modelo deve ser um objeto.")
        predictors = item.get("predictors")
        if not isinstance(predictors, list) or not predictors:
            raise PanelError("Cada modelo deve ter predictors não vazio.")
        fe = str(item.get("fixed_effects", "unit"))
        if fe not in valid_fe:
            raise PanelError(f"fixed_effects inválido: {fe}. Use: {valid_fe}")
        mtype = str(item.get("model_type", "fe"))
        if mtype not in valid_types:
            raise PanelError(f"model_type inválido: {mtype}. Use: {valid_types}")
        models.append(
            ModelSpec(
                name=str(_require(item, "name")),
                target=str(_require(item, "target")),
                predictors=tuple(str(x) for x in predictors),
                fixed_effects=fe,
                model_type=mtype,
                dynamic=bool(item.get("dynamic", False)),
                n_lags=int(item.get("n_lags", 1)),
            )
        )

    weight_items = raw.get("weights", [])
    if not isinstance(weight_items, list):
        raise PanelError("weights deve ser uma lista.")
    weights: list[WeightSpec] = []
    for item in weight_items:
        if not isinstance(item, dict):
            raise PanelError("Cada matriz de pesos deve ser um objeto.")
        transformation = str(item.get("transformation", "row_standardized"))
        if transformation not in {"binary", "row_standardized"}:
            raise PanelError(f"Transformação inválida: {transformation}")
        weights.append(
            WeightSpec(
                name=str(_require(item, "name")),
                path=_resolve(base, str(_require(item, "path"))),
                transformation=transformation,
                origin_column=str(item.get("origin_column", "origin_id")),
                destination_column=str(item.get("destination_column", "destination_id")),
                weight_column=str(item.get("weight_column", "weight")),
                time_varying=bool(item.get("time_varying", False)),
            )
        )

    model_names = [m.name for m in models]
    if len(model_names) != len(set(model_names)):
        raise PanelError("Nomes de modelos devem ser únicos.")

    gap_strategy = str(raw.get("gap_strategy", "none"))
    if gap_strategy not in valid_gaps:
        raise PanelError(f"gap_strategy inválido: {gap_strategy}. Use: {valid_gaps}")

    alpha = float(raw.get("alpha", 0.05))
    if not 0 < alpha < 1:
        raise PanelError("alpha deve estar entre 0 e 1.")

    spatial_models = [m for m in models if m.model_type in ("spatial_lag", "spatial_error")]
    if spatial_models and not weights:
        raise PanelError(
            "Modelos espaciais requerem ao menos uma matriz de pesos em 'weights'."
        )

    return PanelConfig(
        input_path=_resolve(base, str(_require(data, "path"))),
        unit_col=str(_require(data, "unit_col")),
        time_col=str(_require(data, "time_col")),
        geometry_layer=data.get("layer"),
        gap_strategy=gap_strategy,
        gap_limit=int(raw.get("gap_limit", 1)),
        models=tuple(models),
        weights=tuple(weights),
        seed=int(raw.get("seed", 42)),
        alpha=alpha,
        output_dir=_resolve(base, str(_require(output, "dir"))),
    )
