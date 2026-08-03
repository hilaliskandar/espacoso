import pandas as pd
import pytest

from dados_espaciais.errors import DataContractError
from dados_espaciais.validation import (
    join_one_to_one,
    prepare_geometries,
    validate_numeric_columns,
    validate_unique_key,
)


def test_duplicate_key_is_rejected(valid_table: pd.DataFrame):
    duplicated = pd.concat([valid_table, valid_table.iloc[[0]]], ignore_index=True)
    with pytest.raises(DataContractError, match="não é única"):
        validate_unique_key(duplicated, "codigo", "tabela")


def test_missing_crs_is_rejected(valid_spatial):
    no_crs = valid_spatial.copy().set_crs(None, allow_override=True)
    with pytest.raises(DataContractError, match="Falha ao reprojetar"):
        prepare_geometries(no_crs, "EPSG:31983")


def test_invalid_geometry_is_repaired(bowtie_spatial):
    prepared, report = prepare_geometries(bowtie_spatial, "EPSG:3857", True, False)
    assert report.invalid_before == 1
    assert report.invalid_after == 0
    assert report.repaired == 1
    assert prepared.geometry.is_valid.all()


def test_join_reports_unmatched_and_unused(valid_spatial, valid_table):
    table = pd.concat(
        [valid_table.iloc[:2], pd.DataFrame({"codigo": ["Z"], "valor": [9.0]})],
        ignore_index=True,
    )
    joined, report, unmatched, unused = join_one_to_one(
        valid_spatial,
        table,
        spatial_key="id",
        table_key="codigo",
        minimum_match_rate=0.5,
    )
    assert len(joined) == 3
    assert report.matched == 2
    assert report.unmatched_spatial == 1
    assert report.unused_table == 1
    assert unmatched["id"].tolist() == ["C"]
    assert unused["codigo"].tolist() == ["Z"]


def test_join_threshold_is_enforced(valid_spatial, valid_table):
    with pytest.raises(DataContractError, match="abaixo do mínimo"):
        join_one_to_one(
            valid_spatial,
            valid_table.iloc[:1],
            spatial_key="id",
            table_key="codigo",
            minimum_match_rate=0.8,
        )


def test_non_numeric_values_are_rejected():
    frame = pd.DataFrame({"valor": [1, "erro"]})
    with pytest.raises(DataContractError, match="não numéricos"):
        validate_numeric_columns(frame, ["valor"])


def test_join_normalizes_key_types_and_whitespace(valid_spatial):
    spatial = valid_spatial.copy()
    spatial["id"] = [" 1", "2 ", "3"]
    table = pd.DataFrame({"codigo": [1, 2, 3], "valor": [4, 5, 6]})
    joined, report, _, _ = join_one_to_one(
        spatial, table, "id", "codigo", minimum_match_rate=1.0
    )
    assert report.match_rate == 1.0
    assert joined["valor"].tolist() == [4, 5, 6]
