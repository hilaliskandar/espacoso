from __future__ import annotations

import hashlib
import json
import platform
from pathlib import Path

import geopandas as gpd
import matplotlib
import numpy as np
import pandas as pd
import shapely
import yaml


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(data: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def build_manifest(config_path: Path, input_path: Path, outputs: list[Path], seed: int, permutations: int) -> dict:
    return {
        "application": "A2 — matrizes de pesos e autocorrelação espacial",
        "python": platform.python_version(),
        "platform": platform.platform(),
        "versions": {
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "geopandas": gpd.__version__,
            "shapely": shapely.__version__,
            "matplotlib": matplotlib.__version__,
            "pyyaml": yaml.__version__,
        },
        "seed": seed,
        "permutations": permutations,
        "inputs": {
            str(config_path): sha256(config_path),
            str(input_path): sha256(input_path),
        },
        "outputs": {str(path): sha256(path) for path in outputs if path.exists()},
    }
