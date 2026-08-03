from pathlib import Path
import hashlib
import json

import pandas as pd


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_natural_earth_benchmark_contract_and_optional_fixture():
    root = Path(__file__).resolve().parents[1]
    data = root / "data" / "processed" / "natural_earth_countries_v0_4.csv"
    index = root / "data" / "processed" / "natural_earth_country_index_v0_4.csv"
    provenance_path = root / "data" / "processed" / "natural_earth_provenance_v0_4.json"

    provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    assert provenance["benchmark"] == "Natural Earth low-resolution countries"
    assert provenance["n_observations"] == 175
    assert provenance["target"] == "log1p(gdp_md_est)"
    assert provenance["coordinate_columns"] == ["x_km", "y_km"]
    assert provenance["crs_analysis"] == "EPSG:6933"

    if data.exists() and index.exists():
        frame = pd.read_csv(data)
        labels = pd.read_csv(index)
        assert len(frame) == len(labels) == provenance["n_observations"]
        assert _sha256(data) == provenance["processed_csv_sha256"]
        assert _sha256(index) == provenance["country_index_sha256"]
        assert {"x_km", "y_km", "log_gdp_md_est"}.issubset(frame.columns)
        assert frame.isna().sum().sum() == 0
