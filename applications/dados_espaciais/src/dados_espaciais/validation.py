from __future__ import annotations

from dataclasses import asdict, dataclass

import geopandas as gpd
import pandas as pd

from .errors import DataContractError


@dataclass(frozen=True)
class GeometryReport:
    n_features: int
    invalid_before: int
    invalid_after: int
    repaired: int
    empty_geometries: int
    input_crs: str
    analysis_crs: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class JoinReport:
    n_spatial: int
    n_table: int
    matched: int
    unmatched_spatial: int
    unused_table: int
    match_rate: float

    def to_dict(self) -> dict:
        return asdict(self)


def validate_unique_key(frame: pd.DataFrame, key: str, label: str) -> None:
    if key not in frame.columns:
        raise DataContractError(f"Chave ausente em {label}: {key}")
    if frame[key].isna().any():
        raise DataContractError(f"A chave {key} possui valores ausentes em {label}.")
    duplicated = frame.loc[frame[key].duplicated(keep=False), key]
    if not duplicated.empty:
        sample = duplicated.astype(str).unique()[:5].tolist()
        raise DataContractError(
            f"A chave {key} não é única em {label}. Exemplos: {sample}"
        )


def validate_numeric_columns(frame: pd.DataFrame, columns: list[str]) -> None:
    for column in columns:
        if column not in frame.columns:
            raise DataContractError(f"Coluna numérica ausente: {column}")
        converted = pd.to_numeric(frame[column], errors="coerce")
        invalid = converted.isna() & frame[column].notna()
        if invalid.any():
            raise DataContractError(f"A coluna {column} contém valores não numéricos.")
        frame[column] = converted


def prepare_geometries(
    frame: gpd.GeoDataFrame,
    analysis_crs: str,
    repair_invalid: bool = True,
    allow_empty: bool = False,
) -> tuple[gpd.GeoDataFrame, GeometryReport]:
    prepared = frame.copy()
    input_crs = str(prepared.crs)
    invalid_before = int((~prepared.geometry.is_valid).sum())
    if invalid_before and repair_invalid:
        prepared.geometry = prepared.geometry.make_valid()
    invalid_after = int((~prepared.geometry.is_valid).sum())
    empty = int((prepared.geometry.is_empty | prepared.geometry.isna()).sum())
    if invalid_after:
        raise DataContractError(
            f"Persistem {invalid_after} geometrias inválidas após o tratamento."
        )
    if empty and not allow_empty:
        raise DataContractError(f"Foram encontradas {empty} geometrias vazias ou ausentes.")
    try:
        prepared = prepared.to_crs(analysis_crs)
    except Exception as exc:
        raise DataContractError(f"Falha ao reprojetar para {analysis_crs}: {exc}") from exc
    report = GeometryReport(
        n_features=len(prepared),
        invalid_before=invalid_before,
        invalid_after=invalid_after,
        repaired=max(0, invalid_before - invalid_after),
        empty_geometries=empty,
        input_crs=input_crs,
        analysis_crs=str(prepared.crs),
    )
    return prepared, report


def join_one_to_one(
    spatial: gpd.GeoDataFrame,
    table: pd.DataFrame,
    spatial_key: str,
    table_key: str,
    minimum_match_rate: float = 1.0,
) -> tuple[gpd.GeoDataFrame, JoinReport, pd.DataFrame, pd.DataFrame]:
    spatial_work = spatial.copy()
    table_work = table.copy()
    if spatial_key not in spatial_work.columns:
        raise DataContractError(f"Chave ausente em arquivo espacial: {spatial_key}")
    if table_key not in table_work.columns:
        raise DataContractError(f"Chave ausente em tabela: {table_key}")

    spatial_work[spatial_key] = spatial_work[spatial_key].astype("string").str.strip()
    table_work[table_key] = table_work[table_key].astype("string").str.strip()
    validate_unique_key(spatial_work, spatial_key, "arquivo espacial")
    validate_unique_key(table_work, table_key, "tabela")

    table_keys = set(table_work[table_key].dropna())
    spatial_keys = set(spatial_work[spatial_key].dropna())
    matched_keys = spatial_keys & table_keys
    unmatched_keys = spatial_keys - table_keys
    unused_keys = table_keys - spatial_keys

    report = JoinReport(
        n_spatial=len(spatial_work),
        n_table=len(table_work),
        matched=len(matched_keys),
        unmatched_spatial=len(unmatched_keys),
        unused_table=len(unused_keys),
        match_rate=len(matched_keys) / len(spatial_work) if len(spatial_work) else 0.0,
    )
    if not 0 <= minimum_match_rate <= 1:
        raise DataContractError("minimum_match_rate deve estar entre 0 e 1.")
    if report.match_rate < minimum_match_rate:
        raise DataContractError(
            f"Cobertura da junção {report.match_rate:.1%} abaixo do mínimo "
            f"{minimum_match_rate:.1%}."
        )

    table_for_join = table_work.copy()
    if table_key != spatial_key:
        table_for_join = table_for_join.rename(columns={table_key: spatial_key})
    joined = spatial_work.merge(
        table_for_join,
        how="left",
        on=spatial_key,
        validate="one_to_one",
        indicator=True,
    )
    unmatched = joined.loc[joined["_merge"] == "left_only", [spatial_key]].copy()
    unused = table_work.loc[table_work[table_key].isin(unused_keys), [table_key]].copy()
    joined = joined.drop(columns="_merge")
    return joined, report, unmatched, unused
