from pathlib import Path

import pandas as pd
import pytest

from dados_espaciais.cartography import classify, make_choropleth
from dados_espaciais.errors import DataContractError


def test_quantile_classification_preserves_missing_values():
    values = pd.Series([1, 2, 3, 4, None])
    result = classify(values, method="quantiles", k=2)
    assert result.notna().sum() == 4
    assert pd.isna(result.iloc[-1])


def test_unsupported_classification_is_rejected():
    with pytest.raises(DataContractError, match="não suportado"):
        classify(pd.Series([1, 2, 3]), method="jenks", k=3)


def test_map_is_generated(valid_spatial, tmp_path: Path):
    frame = valid_spatial.copy()
    frame["valor"] = [1, 2, 3]
    output = tmp_path / "map.png"
    make_choropleth(frame, "valor", output, "Mapa", k=3)
    assert output.exists()
    assert output.stat().st_size > 0
