"""Testes de carregamento de matrizes de pesos."""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from econometria_espacial.config import WeightSpec
from econometria_espacial.errors import WeightsError
from econometria_espacial.weights import load_weights, matrix_diagnostics


def _write_edges(path: Path, edges: pd.DataFrame) -> None:
    edges.to_csv(path, index=False)


def test_load_weights_basic(tmp_path, grid_4x1):
    _, _, weights_path = grid_4x1
    spec = WeightSpec(name="rook", path=weights_path)
    wm = load_weights(spec, ["A", "B", "C", "D"])
    assert wm.n == 4
    assert wm.s0 == pytest.approx(4.0)  # row-standardized: 4 linhas não-ilhas × 1.0


def test_load_weights_no_islands(tmp_path, grid_4x1):
    _, _, weights_path = grid_4x1
    spec = WeightSpec(name="rook", path=weights_path)
    wm = load_weights(spec, ["A", "B", "C", "D"])
    assert len(wm.islands) == 0


def test_load_weights_missing_file(tmp_path):
    spec = WeightSpec(name="rook", path=tmp_path / "nope.csv")
    with pytest.raises(WeightsError, match="não encontrado"):
        load_weights(spec, ["A", "B"])


def test_load_weights_negative_weight(tmp_path):
    path = tmp_path / "neg.csv"
    _write_edges(path, pd.DataFrame({"origin_id": ["A"], "destination_id": ["B"], "weight": [-1.0]}))
    spec = WeightSpec(name="neg", path=path)
    with pytest.raises(WeightsError, match="negativos"):
        load_weights(spec, ["A", "B"])


def test_matrix_diagnostics(tmp_path, grid_4x1):
    _, _, weights_path = grid_4x1
    spec = WeightSpec(name="rook", path=weights_path)
    wm = load_weights(spec, ["A", "B", "C", "D"])
    diag = matrix_diagnostics(wm)
    assert diag["n"] == 4
    assert diag["islands"] == 0
    assert diag["min_neighbors"] >= 1
