"""Configuração da aplicação de redes e acessibilidade."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from .errors import ConfigError

_ALLOWED_IMPEDANCES = {"linear", "negative_exponential", "binary", "power"}
_ALLOWED_CENTRALITIES = {"betweenness", "closeness", "degree"}


@dataclass(frozen=True)
class ImpedanceSpec:
    name: str
    function: str
    cutoff: float | None = None
    beta: float | None = None
    power: float | None = None


@dataclass(frozen=True)
class AppConfig:
    base_dir: Path
    network_path: Path
    network_layer: str | None
    origins_path: Path
    origins_layer: str | None
    origins_id_column: str
    opportunities_column: str
    population_column: str
    analysis_crs: str
    impedances: tuple[ImpedanceSpec, ...]
    centrality_measures: tuple[str, ...]
    max_cost: float
    seed: int
    output_dir: Path
    maps: bool


def _resolve(base: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else (base / path).resolve()


def _parse_impedance(raw: dict[str, Any], position: int) -> ImpedanceSpec:
    if not isinstance(raw, dict):
        raise ConfigError(f"impedances[{position}] deve ser um objeto.")
    name = str(raw.get("name", "")).strip()
    function = str(raw.get("function", "")).strip().lower()
    if not name:
        raise ConfigError(f"impedances[{position}].name é obrigatório.")
    if function not in _ALLOWED_IMPEDANCES:
        raise ConfigError(
            f"Função de impedância inválida em {name!r}: {function!r}. "
            f"Permitidas: {sorted(_ALLOWED_IMPEDANCES)}."
        )
    cutoff = raw.get("cutoff")
    if cutoff is not None:
        cutoff = float(cutoff)
        if cutoff <= 0:
            raise ConfigError(f"{name}: cutoff deve ser positivo.")
    beta = raw.get("beta")
    if beta is not None:
        beta = float(beta)
        if beta <= 0:
            raise ConfigError(f"{name}: beta deve ser positivo.")
    power = raw.get("power")
    if power is not None:
        power = float(power)
        if power <= 0:
            raise ConfigError(f"{name}: power deve ser positivo.")
    if function == "negative_exponential" and beta is None:
        raise ConfigError(f"{name}: função negative_exponential requer beta.")
    if function == "power" and power is None:
        raise ConfigError(f"{name}: função power requer power.")
    return ImpedanceSpec(name=name, function=function, cutoff=cutoff, beta=beta, power=power)


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

    # network path
    net_path_raw = data.get("network_path")
    if not net_path_raw:
        raise ConfigError("data.network_path é obrigatório.")

    # origins path
    orig_path_raw = data.get("origins_path")
    if not orig_path_raw:
        raise ConfigError("data.origins_path é obrigatório.")

    origins_id = str(data.get("origins_id_column", "")).strip()
    opportunities_col = str(data.get("opportunities_column", "")).strip()
    population_col = str(data.get("population_column", "")).strip()
    crs = str(data.get("analysis_crs", "")).strip()
    if not origins_id or not opportunities_col or not population_col or not crs:
        raise ConfigError(
            "data.origins_id_column, data.opportunities_column, "
            "data.population_column e data.analysis_crs são obrigatórios."
        )

    # impedance specs
    imps_raw = analysis.get("impedances")
    if not isinstance(imps_raw, list) or not imps_raw:
        raise ConfigError("analysis.impedances deve conter ao menos uma função.")
    if len(imps_raw) < 2:
        raise ConfigError("analysis.impedances deve conter ao menos duas funções de impedância.")
    imps = tuple(_parse_impedance(item, i) for i, item in enumerate(imps_raw))
    names = [imp.name for imp in imps]
    if len(names) != len(set(names)):
        raise ConfigError("Os nomes das funções de impedância devem ser únicos.")

    # centrality
    cent_raw = analysis.get("centrality", [])
    if not isinstance(cent_raw, list):
        raise ConfigError("analysis.centrality deve ser uma lista.")
    for c in cent_raw:
        if c not in _ALLOWED_CENTRALITIES:
            raise ConfigError(f"Medida de centralidade inválida: {c!r}.")

    max_cost = float(analysis.get("max_cost", 1e9))
    if max_cost <= 0:
        raise ConfigError("analysis.max_cost deve ser positivo.")

    return AppConfig(
        base_dir=base,
        network_path=_resolve(base, str(net_path_raw)),
        network_layer=(str(data.get("network_layer")).strip() if data.get("network_layer") else None),
        origins_path=_resolve(base, str(orig_path_raw)),
        origins_layer=(str(data.get("origins_layer")).strip() if data.get("origins_layer") else None),
        origins_id_column=origins_id,
        opportunities_column=opportunities_col,
        population_column=population_col,
        analysis_crs=crs,
        impedances=imps,
        centrality_measures=tuple(cent_raw),
        max_cost=max_cost,
        seed=int(analysis.get("seed", 20260804)),
        output_dir=_resolve(base, str(output.get("directory", "../outputs/run"))),
        maps=bool(output.get("maps", True)),
    )
