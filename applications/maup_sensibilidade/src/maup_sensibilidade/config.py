from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from .errors import ConfigError


@dataclass(frozen=True)
class SchemeSpec:
    """Especificação de um esquema territorial."""

    name: str
    """Rótulo curto do esquema (ex.: 'micro', 'meso', 'macro')."""
    dissolve_column: str | None
    """Coluna da camada base usada para dissolução. None = usar a própria geometria."""
    weight_column: str | None
    """Coluna numérica de ponderação para médias ponderadas. None = pesos iguais."""


@dataclass(frozen=True)
class AnalysisConfig:
    input_path: Path
    id_column: str
    geometry_layer: str | None
    variables: tuple[str, ...]
    schemes: tuple[SchemeSpec, ...]
    permutations: int
    seed: int
    alpha: float
    output_dir: Path
    classes: int = 5
    colormap: str = "YlOrRd"


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

    variables = _require(raw, "variables")
    if not isinstance(variables, list) or not variables:
        raise ConfigError("variables deve conter ao menos uma variável.")

    scheme_items = _require(raw, "schemes")
    if not isinstance(scheme_items, list) or len(scheme_items) < 2:
        raise ConfigError("schemes deve conter ao menos dois esquemas para comparação.")
    schemes: list[SchemeSpec] = []
    seen_names: set[str] = set()
    for item in scheme_items:
        if not isinstance(item, dict):
            raise ConfigError("Cada esquema deve ser um objeto.")
        name = str(_require(item, "name"))
        if name in seen_names:
            raise ConfigError(f"Nome de esquema duplicado: {name}")
        seen_names.add(name)
        schemes.append(
            SchemeSpec(
                name=name,
                dissolve_column=item.get("dissolve_column"),
                weight_column=item.get("weight_column"),
            )
        )

    permutations = int(raw.get("permutations", 999))
    if permutations < 99:
        raise ConfigError("permutations deve ser >= 99.")
    alpha = float(raw.get("alpha", 0.05))
    if not 0 < alpha < 1:
        raise ConfigError("alpha deve estar entre 0 e 1.")
    classes = int(raw.get("classes", 5))
    if classes < 2:
        raise ConfigError("classes deve ser >= 2.")

    return AnalysisConfig(
        input_path=_resolve(base, str(_require(data, "path"))),
        id_column=str(_require(data, "id_column")),
        geometry_layer=data.get("layer"),
        variables=tuple(str(v) for v in variables),
        schemes=tuple(schemes),
        permutations=permutations,
        seed=int(raw.get("seed", 42)),
        alpha=alpha,
        output_dir=_resolve(base, str(_require(output, "dir"))),
        classes=classes,
        colormap=str(raw.get("colormap", "YlOrRd")),
    )
