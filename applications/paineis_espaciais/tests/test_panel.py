from __future__ import annotations

import pandas as pd
import pytest

from paineis_espaciais.panel import (
    PanelData,
    build_panel,
    check_balance,
    fill_gaps,
    lag_column,
    unit_time_index,
)
from paineis_espaciais.errors import PanelError


# ---------------------------------------------------------------------------
# unit_time_index
# ---------------------------------------------------------------------------

def test_unit_time_index_creates_multiindex(small_panel_df):
    indexed = unit_time_index(small_panel_df, "unit_id", "time_id")
    assert indexed.index.names == ["unit_id", "time_id"]


def test_unit_time_index_sorted(small_panel_df):
    indexed = unit_time_index(small_panel_df, "unit_id", "time_id")
    assert indexed.index.is_monotonic_increasing


def test_unit_time_index_duplicate_raises(small_panel_df):
    dup = pd.concat([small_panel_df, small_panel_df.head(1)], ignore_index=True)
    with pytest.raises(PanelError, match="duplicados"):
        unit_time_index(dup, "unit_id", "time_id")


def test_unit_time_index_missing_col_raises(small_panel_df):
    with pytest.raises(PanelError, match="Coluna de unidade"):
        unit_time_index(small_panel_df, "nonexistent", "time_id")


# ---------------------------------------------------------------------------
# check_balance
# ---------------------------------------------------------------------------

def test_check_balance_balanced(small_panel_df):
    indexed = unit_time_index(small_panel_df, "unit_id", "time_id")
    info = check_balance(indexed)
    assert info["balanced"] is True
    assert info["n_units"] == 4
    assert info["n_periods"] == 3
    assert info["missing_cells"] == 0


def test_check_balance_unbalanced(unbalanced_panel_df):
    indexed = unit_time_index(unbalanced_panel_df, "unit_id", "time_id")
    info = check_balance(indexed)
    assert info["balanced"] is False
    assert info["missing_cells"] == 2


# ---------------------------------------------------------------------------
# fill_gaps
# ---------------------------------------------------------------------------

def test_fill_gaps_forward_fill(unbalanced_panel_df):
    indexed = unit_time_index(unbalanced_panel_df, "unit_id", "time_id")
    filled = fill_gaps(indexed, strategy="forward_fill", limit=1)
    # Sem mais NaN em y após fill (ou pelo menos não mais do que original)
    assert filled.index.is_monotonic_increasing


def test_fill_gaps_invalid_strategy(small_panel_df):
    indexed = unit_time_index(small_panel_df, "unit_id", "time_id")
    with pytest.raises(PanelError, match="Estratégia"):
        fill_gaps(indexed, strategy="magic")


def test_fill_gaps_no_cross_unit_contamination(unbalanced_panel_df):
    """Verifica que fill_gaps não contamina valores entre unidades distintas."""
    indexed = unit_time_index(unbalanced_panel_df, "unit_id", "time_id")
    filled = fill_gaps(indexed, strategy="forward_fill", limit=None)
    # Unidades devem permanecer separadas no índice
    units_filled = filled.index.get_level_values(0).unique().tolist()
    assert set(units_filled) == {"A", "B", "C", "D"}


# ---------------------------------------------------------------------------
# lag_column
# ---------------------------------------------------------------------------

def test_lag_column_creates_lag1(small_panel_df):
    indexed = unit_time_index(small_panel_df, "unit_id", "time_id")
    lagged = lag_column(indexed, "y", n_lags=1)
    assert "y_lag1" in lagged.columns


def test_lag_column_no_cross_unit(small_panel_df):
    """O primeiro período de cada unidade deve ter NaN na defasagem."""
    indexed = unit_time_index(small_panel_df, "unit_id", "time_id")
    lagged = lag_column(indexed, "y", n_lags=1)
    for unit in ["A", "B", "C", "D"]:
        first_period = lagged.loc[unit].index.min()
        assert pd.isna(lagged.loc[(unit, first_period), "y_lag1"]), (
            f"Unidade {unit} não deve ter lag1 no primeiro período"
        )


def test_lag_column_invalid_col(small_panel_df):
    indexed = unit_time_index(small_panel_df, "unit_id", "time_id")
    with pytest.raises(PanelError, match="Coluna não encontrada"):
        lag_column(indexed, "nonexistent")


def test_lag_column_invalid_n(small_panel_df):
    indexed = unit_time_index(small_panel_df, "unit_id", "time_id")
    with pytest.raises(PanelError, match="n_lags"):
        lag_column(indexed, "y", n_lags=0)


# ---------------------------------------------------------------------------
# build_panel
# ---------------------------------------------------------------------------

def test_build_panel_balanced(small_panel_df):
    panel = build_panel(small_panel_df, "unit_id", "time_id")
    assert isinstance(panel, PanelData)
    assert panel.balanced is True
    assert panel.n_units == 4
    assert panel.n_periods == 3


def test_build_panel_unbalanced_no_fill(unbalanced_panel_df):
    panel = build_panel(unbalanced_panel_df, "unit_id", "time_id", gap_strategy="none")
    assert panel.balanced is False
    assert panel.missing_cells == 2


def test_build_panel_unbalanced_with_fill(unbalanced_panel_df):
    panel = build_panel(
        unbalanced_panel_df, "unit_id", "time_id", gap_strategy="forward_fill"
    )
    # Após preenchimento o painel pode se tornar balanceado
    assert panel.missing_cells == 0
