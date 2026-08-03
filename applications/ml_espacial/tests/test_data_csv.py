import pandas as pd
import pytest

from src.data import load_csv_spatial


def test_load_csv_spatial(tmp_path):
    path = tmp_path / "sample.csv"
    pd.DataFrame(
        {
            "longitude": [-120.0, -121.0, -122.0],
            "latitude": [35.0, 36.0, 37.0],
            "x": [1.0, 2.0, 3.0],
            "median_house_value": [2.0, 3.0, 4.0],
            "text": ["a", "b", "c"],
        }
    ).to_csv(path, index=False)
    ds = load_csv_spatial(path, "median_house_value", ("longitude", "latitude"))
    assert len(ds.frame) == 3
    assert "text" not in ds.frame.columns
    assert ds.target_column == "median_house_value"


def test_load_csv_spatial_missing_columns(tmp_path):
    path = tmp_path / "bad.csv"
    pd.DataFrame({"longitude": [1.0]}).to_csv(path, index=False)
    with pytest.raises(ValueError):
        load_csv_spatial(path, "target", ("longitude", "latitude"))
