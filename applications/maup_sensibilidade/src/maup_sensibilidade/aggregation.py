from __future__ import annotations

"""Rotinas de agregação territorial para análise MAUP.

Cada função recebe um GeoDataFrame de unidades base e retorna um GeoDataFrame
agregado, preservando chaves auditáveis e ponderações explícitas.
"""

import geopandas as gpd
import numpy as np
import pandas as pd

from .config import SchemeSpec
from .errors import AggregationError


def _weighted_mean(values: pd.Series, weights: pd.Series | None) -> float:
    """Média ponderada; se weights é None, retorna a média simples."""
    v = np.asarray(values, dtype=float)
    if weights is None or weights.isna().all():
        return float(np.mean(v))
    w = np.asarray(weights, dtype=float)
    w = np.where(np.isfinite(w) & (w > 0), w, 0.0)
    total = float(np.sum(w))
    if total <= 0.0:
        return float(np.mean(v))
    return float(np.dot(w, v) / total)


def _weighted_std(values: pd.Series, weights: pd.Series | None) -> float:
    """Desvio-padrão ponderado (ddof=0)."""
    v = np.asarray(values, dtype=float)
    if weights is None or weights.isna().all():
        return float(np.std(v, ddof=0))
    w = np.asarray(weights, dtype=float)
    w = np.where(np.isfinite(w) & (w > 0), w, 0.0)
    total = float(np.sum(w))
    if total <= 0.0:
        return float(np.std(v, ddof=0))
    mean = float(np.dot(w, v) / total)
    return float(np.sqrt(np.dot(w, (v - mean) ** 2) / total))


def aggregate(
    gdf: gpd.GeoDataFrame,
    scheme: SchemeSpec,
    variables: tuple[str, ...],
) -> gpd.GeoDataFrame:
    """Agrega *gdf* segundo *scheme*, retornando um GeoDataFrame com:

    - geometria dissolvida (union);
    - chave ``scheme_id`` com o identificador do agregado;
    - chave ``n_units`` com a contagem de unidades base;
    - para cada variável: média e desvio-padrão ponderados;
    - soma de variáveis (para teste de conservação de totais).
    """
    if scheme.dissolve_column is not None and scheme.dissolve_column not in gdf.columns:
        raise AggregationError(
            f"Coluna de dissolução ausente: {scheme.dissolve_column!r}"
        )
    if scheme.weight_column is not None and scheme.weight_column not in gdf.columns:
        raise AggregationError(
            f"Coluna de ponderação ausente: {scheme.weight_column!r}"
        )

    work = gdf.copy()

    if scheme.dissolve_column is None:
        # Sem dissolução: cada unidade base é seu próprio agregado.
        work["_group"] = work.index.astype(str)
    else:
        work["_group"] = work[scheme.dissolve_column].astype(str)

    records: list[dict] = []
    geoms: list = []

    for group_key, sub in work.groupby("_group", sort=True):
        record: dict = {
            "scheme_id": str(group_key),
            "scheme_name": scheme.name,
            "n_units": len(sub),
        }
        w_col = sub[scheme.weight_column] if scheme.weight_column else None
        for var in variables:
            record[f"{var}_mean"] = _weighted_mean(sub[var], w_col)
            record[f"{var}_std"] = _weighted_std(sub[var], w_col)
            record[f"{var}_sum"] = float(sub[var].sum())
            record[f"{var}_min"] = float(sub[var].min())
            record[f"{var}_max"] = float(sub[var].max())
        records.append(record)
        geoms.append(sub.union_all())

    result = gpd.GeoDataFrame(records, geometry=geoms, crs=gdf.crs)
    result = result.set_index("scheme_id").reset_index()
    return result


def verify_total_conservation(
    base: gpd.GeoDataFrame,
    aggregated: gpd.GeoDataFrame,
    variables: tuple[str, ...],
    rtol: float = 1e-6,
) -> dict[str, bool]:
    """Verifica conservação de totais para cada variável.

    Retorna dict {variável: True se conservado, False caso contrário}.
    """
    result: dict[str, bool] = {}
    for var in variables:
        base_total = float(base[var].sum())
        agg_total = float(aggregated[f"{var}_sum"].sum())
        result[var] = bool(np.isclose(base_total, agg_total, rtol=rtol))
    return result
