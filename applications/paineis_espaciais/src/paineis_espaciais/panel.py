from __future__ import annotations

"""Estrutura de dados e operações fundamentais para painéis espaço-temporais."""

from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd

from .errors import PanelError


@dataclass
class PanelData:
    """Painel organizado com índice (unidade, tempo).

    Attributes
    ----------
    data:
        DataFrame com MultiIndex (unit_id, time_id) já ordenado.
    unit_col:
        Nome da coluna de identificação de unidade.
    time_col:
        Nome da coluna de identificação de período.
    balanced:
        Indica se todas as unidades têm o mesmo número de períodos.
    n_units:
        Número de unidades espaciais.
    n_periods:
        Número de períodos distintos.
    missing_cells:
        Número de células ausentes (unidade × período) para painel desbalanceado.
    """

    data: pd.DataFrame
    unit_col: str
    time_col: str
    balanced: bool
    n_units: int
    n_periods: int
    missing_cells: int
    metadata: dict[str, Any] = field(default_factory=dict)


def unit_time_index(df: pd.DataFrame, unit_col: str, time_col: str) -> pd.DataFrame:
    """Garante índice (unit, time) único e ordenado, sem contaminação entre unidades.

    Parameters
    ----------
    df:
        DataFrame com colunas *unit_col* e *time_col*.
    unit_col:
        Coluna que identifica a unidade espacial.
    time_col:
        Coluna que identifica o período.

    Returns
    -------
    pd.DataFrame
        DataFrame com MultiIndex (unit_col, time_col) ordenado.

    Raises
    ------
    PanelError
        Se existirem pares (unit, time) duplicados.
    """
    if unit_col not in df.columns:
        raise PanelError(f"Coluna de unidade não encontrada: {unit_col}")
    if time_col not in df.columns:
        raise PanelError(f"Coluna de tempo não encontrada: {time_col}")

    indexed = df.set_index([unit_col, time_col]).sort_index()
    duplicates = indexed.index.duplicated()
    if duplicates.any():
        bad = indexed.index[duplicates].tolist()[:5]
        raise PanelError(
            f"Índices (unidade, tempo) duplicados detectados: {bad}"
        )
    return indexed


def check_balance(df: pd.DataFrame) -> dict[str, Any]:
    """Verifica se o painel é balanceado.

    Parameters
    ----------
    df:
        DataFrame com MultiIndex (unit, time) — saída de :func:`unit_time_index`.

    Returns
    -------
    dict
        ``balanced`` bool, ``n_units``, ``n_periods``, ``missing_cells``,
        ``counts_per_unit``.
    """
    units = df.index.get_level_values(0).unique()
    times = df.index.get_level_values(1).unique()
    n_units = len(units)
    n_periods = len(times)

    counts = df.groupby(level=0).size()
    balanced = bool((counts == n_periods).all())
    missing_cells = int(n_units * n_periods - len(df))

    return {
        "balanced": balanced,
        "n_units": n_units,
        "n_periods": n_periods,
        "missing_cells": missing_cells,
        "counts_per_unit": counts.to_dict(),
    }


def fill_gaps(
    df: pd.DataFrame,
    strategy: str = "forward_fill",
    limit: int | None = 1,
) -> pd.DataFrame:
    """Trata lacunas em painel desbalanceado.

    O preenchimento é feito **dentro de cada unidade**, sem contaminação
    entre unidades espaciais distintas.

    Parameters
    ----------
    df:
        DataFrame com MultiIndex (unit, time) — saída de :func:`unit_time_index`.
    strategy:
        ``"forward_fill"`` (padrão), ``"backward_fill"`` ou ``"interpolate"``.
    limit:
        Número máximo de períodos consecutivos a preencher (None = sem limite).

    Returns
    -------
    pd.DataFrame
        DataFrame com lacunas preenchidas conforme a estratégia.

    Raises
    ------
    PanelError
        Se a estratégia for inválida.
    """
    valid = {"forward_fill", "backward_fill", "interpolate"}
    if strategy not in valid:
        raise PanelError(f"Estratégia de preenchimento inválida: {strategy}. Use: {valid}")

    units = df.index.get_level_values(0).unique()
    times = df.index.get_level_values(1).unique()
    full_index = pd.MultiIndex.from_product([units, times], names=df.index.names)
    df_full = df.reindex(full_index)

    result_parts: list[pd.DataFrame] = []
    for unit, group in df_full.groupby(level=0, sort=False):
        group_sorted = group.sort_index(level=1)
        if strategy == "forward_fill":
            filled = group_sorted.ffill(limit=limit)
        elif strategy == "backward_fill":
            filled = group_sorted.bfill(limit=limit)
        else:
            filled = group_sorted.interpolate(method="linear", limit=limit, limit_direction="both")
        result_parts.append(filled)

    return pd.concat(result_parts).sort_index()


def lag_column(
    df: pd.DataFrame,
    column: str,
    n_lags: int = 1,
) -> pd.DataFrame:
    """Cria defasagens temporais sem contaminação entre unidades.

    A defasagem é calculada **dentro de cada unidade** com base na ordenação
    natural do índice temporal. Períodos iniciais recebem NaN.

    Parameters
    ----------
    df:
        DataFrame com MultiIndex (unit, time) — saída de :func:`unit_time_index`.
    column:
        Coluna a ser defasada.
    n_lags:
        Número de períodos de defasagem.

    Returns
    -------
    pd.DataFrame
        DataFrame original acrescido de coluna(s) ``{column}_lag{n}`` para
        cada ``n`` em ``range(1, n_lags + 1)``.
    """
    if column not in df.columns:
        raise PanelError(f"Coluna não encontrada no painel: {column}")
    if n_lags < 1:
        raise PanelError("n_lags deve ser >= 1.")

    result = df.copy()
    for n in range(1, n_lags + 1):
        lag_name = f"{column}_lag{n}"
        result[lag_name] = (
            result[column]
            .groupby(level=0)
            .shift(n)
        )
    return result


def build_panel(
    df: pd.DataFrame,
    unit_col: str,
    time_col: str,
    gap_strategy: str = "none",
    gap_limit: int | None = 1,
) -> PanelData:
    """Constrói um :class:`PanelData` a partir de um DataFrame simples.

    Parameters
    ----------
    df:
        DataFrame com colunas *unit_col* e *time_col* e variáveis de análise.
    unit_col:
        Coluna de identificação de unidade.
    time_col:
        Coluna de identificação de período.
    gap_strategy:
        ``"none"`` (manter lacunas), ``"forward_fill"``, ``"backward_fill"``
        ou ``"interpolate"``.
    gap_limit:
        Limite de períodos para preenchimento (ignorado se ``gap_strategy="none"``).

    Returns
    -------
    PanelData
    """
    indexed = unit_time_index(df, unit_col, time_col)
    balance = check_balance(indexed)

    if gap_strategy != "none" and balance["missing_cells"] > 0:
        indexed = fill_gaps(indexed, strategy=gap_strategy, limit=gap_limit)
        balance = check_balance(indexed)

    return PanelData(
        data=indexed,
        unit_col=unit_col,
        time_col=time_col,
        balanced=balance["balanced"],
        n_units=balance["n_units"],
        n_periods=balance["n_periods"],
        missing_cells=balance["missing_cells"],
    )
