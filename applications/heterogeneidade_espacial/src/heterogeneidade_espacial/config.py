from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from .errors import ConfigError

VALID_KERNELS = {"gaussian", "bisquare", "exponential"}
VALID_BANDWIDTH_METHODS = {"golden_section", "interval"}
VALID_FIXED_OR_ADAPTIVE = {"fixed", "adaptive"}


@dataclass(frozen=True)
class GlobalModelSpec:
    target: str
    predictors: tuple[str, ...]
    add_constant: bool = True
    robust_covariance: str = "HC3"


@dataclass(frozen=True)
class BandwidthSpec:
    criterion: str = "AICc"
    kernel: str = "bisquare"
    fixed_or_adaptive: str = "adaptive"
    search_method: str = "golden_section"
    min_bandwidth: float | None = None
    max_bandwidth: float | None = None


@dataclass(frozen=True)
class AnalysisConfig:
    input_path: Path
    id_column: str
    geometry_layer: str | None
    target: str
    predictors: tuple[str, ...]
    add_constant: bool
    robust_covariance: str
    bandwidth: BandwidthSpec
    run_mgwr: bool
    mgwr_bandwidth: BandwidthSpec
    permutations: int
    seed: int
    alpha: float
    output_dir: Path
    n_bootstrap: int = 0
    bootstrap_fraction: float = 0.8


def _resolve(base: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else (base / path).resolve()


def _require(mapping: dict[str, Any], key: str) -> Any:
    if key not in mapping:
        raise ConfigError(f"Campo obrigatório ausente: {key}")
    return mapping[key]


def _parse_bandwidth(raw: dict[str, Any]) -> BandwidthSpec:
    criterion = str(raw.get("criterion", "AICc"))
    kernel = str(raw.get("kernel", "bisquare"))
    fixed_or_adaptive = str(raw.get("fixed_or_adaptive", "adaptive"))
    search_method = str(raw.get("search_method", "golden_section"))
    if kernel not in VALID_KERNELS:
        raise ConfigError(f"Kernel inválido: {kernel}. Válidos: {VALID_KERNELS}")
    if fixed_or_adaptive not in VALID_FIXED_OR_ADAPTIVE:
        raise ConfigError(f"fixed_or_adaptive inválido: {fixed_or_adaptive}")
    if search_method not in VALID_BANDWIDTH_METHODS:
        raise ConfigError(f"search_method inválido: {search_method}")
    min_bw = float(raw["min_bandwidth"]) if "min_bandwidth" in raw else None
    max_bw = float(raw["max_bandwidth"]) if "max_bandwidth" in raw else None
    return BandwidthSpec(
        criterion=criterion,
        kernel=kernel,
        fixed_or_adaptive=fixed_or_adaptive,
        search_method=search_method,
        min_bandwidth=min_bw,
        max_bandwidth=max_bw,
    )


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

    model = _require(raw, "model")
    if not isinstance(model, dict):
        raise ConfigError("model deve ser um objeto.")

    predictors = model.get("predictors")
    if not isinstance(predictors, list) or not predictors:
        raise ConfigError("model.predictors deve conter ao menos um preditor.")

    robust = str(model.get("robust_covariance", "HC3")).upper()
    if robust not in {"HC0", "HC1", "HC2", "HC3"}:
        raise ConfigError(f"Covariância robusta não suportada: {robust}")

    bw_raw = raw.get("bandwidth", {})
    if not isinstance(bw_raw, dict):
        raise ConfigError("bandwidth deve ser um objeto.")
    bandwidth = _parse_bandwidth(bw_raw)

    mgwr_bw_raw = raw.get("mgwr_bandwidth", bw_raw)
    if not isinstance(mgwr_bw_raw, dict):
        raise ConfigError("mgwr_bandwidth deve ser um objeto.")
    mgwr_bandwidth = _parse_bandwidth(mgwr_bw_raw)

    permutations = int(raw.get("permutations", 99))
    if permutations < 99:
        raise ConfigError("permutations deve ser >= 99.")
    alpha = float(raw.get("alpha", 0.05))
    if not 0 < alpha < 1:
        raise ConfigError("alpha deve estar entre 0 e 1.")

    n_bootstrap = int(raw.get("n_bootstrap", 0))
    bootstrap_fraction = float(raw.get("bootstrap_fraction", 0.8))
    if not 0 < bootstrap_fraction <= 1:
        raise ConfigError("bootstrap_fraction deve estar entre 0 e 1 (exclusive 0).")

    return AnalysisConfig(
        input_path=_resolve(base, str(_require(data, "path"))),
        id_column=str(_require(data, "id_column")),
        geometry_layer=data.get("layer"),
        target=str(_require(model, "target")),
        predictors=tuple(str(x) for x in predictors),
        add_constant=bool(model.get("add_constant", True)),
        robust_covariance=robust,
        bandwidth=bandwidth,
        run_mgwr=bool(raw.get("run_mgwr", True)),
        mgwr_bandwidth=mgwr_bandwidth,
        permutations=permutations,
        seed=int(raw.get("seed", 42)),
        alpha=alpha,
        output_dir=_resolve(base, str(_require(output, "dir"))),
        n_bootstrap=n_bootstrap,
        bootstrap_fraction=bootstrap_fraction,
    )
