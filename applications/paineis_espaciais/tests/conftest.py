from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def small_panel_df() -> pd.DataFrame:
    """Painel balanceado 4 unidades × 3 períodos."""
    rows = []
    for unit in ["A", "B", "C", "D"]:
        for t in [2020, 2021, 2022]:
            rows.append(
                {
                    "unit_id": unit,
                    "time_id": t,
                    "x1": float(hash((unit, t, "x1")) % 100) / 10,
                    "x2": float(hash((unit, t, "x2")) % 50) / 10,
                    "y": float(hash((unit, t, "y")) % 200) / 10,
                }
            )
    return pd.DataFrame(rows)


@pytest.fixture
def unbalanced_panel_df(small_panel_df: pd.DataFrame) -> pd.DataFrame:
    """Painel desbalanceado com 2 linhas removidas."""
    return small_panel_df.drop(index=[0, 5]).reset_index(drop=True)


@pytest.fixture
def queen_weights_df() -> pd.DataFrame:
    """Pesos rainha para 4 unidades em linha (A-B-C-D)."""
    edges = [
        ("A", "B", 0.5), ("A", "C", 0.5),
        ("B", "A", 1/3), ("B", "C", 1/3), ("B", "D", 1/3),
        ("C", "A", 1/3), ("C", "B", 1/3), ("C", "D", 1/3),
        ("D", "B", 0.5), ("D", "C", 0.5),
    ]
    return pd.DataFrame(edges, columns=["origin_id", "destination_id", "weight"])


@pytest.fixture
def queen_weights_path(tmp_path: Path, queen_weights_df: pd.DataFrame) -> Path:
    path = tmp_path / "pesos_queen.csv"
    queen_weights_df.to_csv(path, index=False)
    return path


@pytest.fixture
def panel_csv_path(tmp_path: Path, small_panel_df: pd.DataFrame) -> Path:
    path = tmp_path / "painel.csv"
    small_panel_df.to_csv(path, index=False)
    return path


@pytest.fixture
def unbalanced_csv_path(tmp_path: Path, unbalanced_panel_df: pd.DataFrame) -> Path:
    path = tmp_path / "painel_unbal.csv"
    unbalanced_panel_df.to_csv(path, index=False)
    return path


@pytest.fixture
def W_4x4(queen_weights_df: pd.DataFrame) -> np.ndarray:
    """Matriz densa 4×4 a partir dos pesos rainha."""
    ids = ["A", "B", "C", "D"]
    idx = {u: i for i, u in enumerate(ids)}
    W = np.zeros((4, 4))
    for _, row in queen_weights_df.iterrows():
        W[idx[row["origin_id"]], idx[row["destination_id"]]] = row["weight"]
    return W
