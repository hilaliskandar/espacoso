from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from diagnostico_ols.config import WeightSpec
from diagnostico_ols.errors import WeightsError
from diagnostico_ols.weights import load_weights


def test_row_standardizes_weights(four_grid):
    _, _, path = four_grid
    spec = WeightSpec(name="line", path=path)
    weights = load_weights(spec, ["A", "B", "C", "D"])
    row_sums = np.asarray(weights.matrix.sum(axis=1)).ravel()
    assert np.allclose(row_sums, 1.0)
    assert weights.islands == ()


def test_preserves_data_order(four_grid):
    _, _, path = four_grid
    spec = WeightSpec(name="line", path=path)
    weights = load_weights(spec, ["D", "C", "B", "A"])
    assert weights.ids == ("D", "C", "B", "A")
    assert weights.matrix[0, 1] == pytest.approx(1.0)


def test_rejects_unknown_identifier(tmp_path: Path):
    path = tmp_path / "w.csv"
    pd.DataFrame({"origin_id": ["A"], "destination_id": ["X"], "weight": [1.0]}).to_csv(path, index=False)
    with pytest.raises(WeightsError):
        load_weights(WeightSpec(name="bad", path=path), ["A", "B"])
