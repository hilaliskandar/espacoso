from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from .errors import ConfigError


_ALLOWED_WEIGHT_TYPES = {"rook", "queen", "knn", "distance"}
_ALLOWED_TRANSFORMS = {"binary", "row_standardized"}
_ALLOWED_SYMMETRIZATION = {"union", "mutual", "none"}
_ALLOWED_ALTERNATIVES = {"two-sided", "greater", "less"}


@dataclass(frozen=True)
class WeightSpec:
    name: str
    type: str
    transform: str = "row_standardized"
    k: int | None = None
    threshold: float | None = None
    distance_power: float = 0.0
    symmetrization: str = "union"
    boundary_tolerance: float = 1e-9


@dataclass(frozen=True)
class AppConfig:
    base_dir: Path
    input_path: Path
    input_layer: str | None
    id_column: str
    value_column: str
    analysis_crs: str
    weights: tuple[WeightSpec, ...]
    primary_weight: str
    permutations: int
    seed: int
    alpha: float
    alternative: str
    fdr: bool
    output_dir: Path
    maps: bool


def _resolve(base: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else (base / path).resolve()


def _parse_weight(raw: dict[str, Any], position: int) -> WeightSpec:
    if not isinstance(raw, dict):
        raise ConfigError(f"weights[{position}] deve ser um objeto.")
    name = str(raw.get("name", "")).strip()
    kind = str(raw.get("type", "")).strip().lower()
    if not name:
        raise ConfigError(f"weights[{position}].name é obrigatório.")
    if kind not in _ALLOWED_WEIGHT_TYPES:
        raise ConfigError(f"Tipo de peso inválido em {name}: {kind!r}.")
    transform = str(raw.get("transform", "row_standardized")).strip().lower()
    if transform not in _ALLOWED_TRANSFORMS:
        raise ConfigError(f"Transformação inválida em {name}: {transform!r}.")
    sym = str(raw.get("symmetrization", "union")).strip().lower()
    if sym not in _ALLOWED_SYMMETRIZATION:
        raise ConfigError(f"Simetrização inválida em {name}: {sym!r}.")
    k = raw.get("k")
    threshold = raw.get("threshold")
    power = float(raw.get("distance_power", 0.0))
    tolerance = float(raw.get("boundary_tolerance", 1e-9))
    if kind == "knn":
        if k is None or int(k) < 1:
            raise ConfigError(f"{name}: k deve ser inteiro positivo.")
        k = int(k)
    elif k is not None:
        k = int(k)
    if kind == "distance":
        if threshold is None or float(threshold) <= 0:
            raise ConfigError(f"{name}: threshold deve ser positivo.")
        threshold = float(threshold)
        if power < 0:
            raise ConfigError(f"{name}: distance_power não pode ser negativo.")
    elif threshold is not None:
        threshold = float(threshold)
    if tolerance < 0:
        raise ConfigError(f"{name}: boundary_tolerance não pode ser negativo.")
    return WeightSpec(
        name=name,
        type=kind,
        transform=transform,
        k=k,
        threshold=threshold,
        distance_power=power,
        symmetrization=sym,
        boundary_tolerance=tolerance,
    )


def load_config(path: str | Path) -> AppConfig:
    config_path = Path(path).resolve()
    if not config_path.exists():
        raise ConfigError(f"Configuração não encontrada: {config_path}")
    raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ConfigError("A configuração YAML deve conter um objeto na raiz.")
    base = config_path.parent
    data = raw.get("data", {})
    analysis = raw.get("analysis", {})
    output = raw.get("output", {})
    if not isinstance(data, dict) or not isinstance(analysis, dict) or not isinstance(output, dict):
        raise ConfigError("As seções data, analysis e output devem ser objetos.")

    specs_raw = analysis.get("weights")
    if not isinstance(specs_raw, list) or not specs_raw:
        raise ConfigError("analysis.weights deve conter ao menos uma matriz.")
    specs = tuple(_parse_weight(item, i) for i, item in enumerate(specs_raw))
    names = [spec.name for spec in specs]
    if len(names) != len(set(names)):
        raise ConfigError("Os nomes das matrizes de pesos devem ser únicos.")
    primary = str(analysis.get("primary_weight", names[0])).strip()
    if primary not in names:
        raise ConfigError("analysis.primary_weight deve corresponder a uma matriz declarada.")

    permutations = int(analysis.get("permutations", 999))
    if permutations < 19:
        raise ConfigError("analysis.permutations deve ser pelo menos 19.")
    alpha = float(analysis.get("alpha", 0.05))
    if not 0 < alpha < 1:
        raise ConfigError("analysis.alpha deve estar entre 0 e 1.")
    alternative = str(analysis.get("alternative", "two-sided")).strip().lower()
    if alternative not in _ALLOWED_ALTERNATIVES:
        raise ConfigError("analysis.alternative inválida.")

    input_value = data.get("path")
    if not input_value:
        raise ConfigError("data.path é obrigatório.")
    id_column = str(data.get("id_column", "")).strip()
    value_column = str(data.get("value_column", "")).strip()
    crs = str(data.get("analysis_crs", "")).strip()
    if not id_column or not value_column or not crs:
        raise ConfigError("data.id_column, data.value_column e data.analysis_crs são obrigatórios.")

    return AppConfig(
        base_dir=base,
        input_path=_resolve(base, str(input_value)),
        input_layer=(str(data.get("layer")).strip() if data.get("layer") else None),
        id_column=id_column,
        value_column=value_column,
        analysis_crs=crs,
        weights=specs,
        primary_weight=primary,
        permutations=permutations,
        seed=int(analysis.get("seed", 20260803)),
        alpha=alpha,
        alternative=alternative,
        fdr=bool(analysis.get("fdr", True)),
        output_dir=_resolve(base, str(output.get("directory", "../outputs/run"))),
        maps=bool(output.get("maps", True)),
    )
