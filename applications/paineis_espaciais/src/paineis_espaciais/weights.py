from __future__ import annotations

"""Construção e diagnóstico de matrizes de pesos espaciais para painéis."""

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import scipy.sparse as sp

from .errors import PanelError


@dataclass(frozen=True)
class WeightSpec:
    """Especificação de uma matriz de pesos espaciais.

    Attributes
    ----------
    name:
        Identificador da matriz.
    path:
        Caminho para o arquivo CSV com colunas (origin_id, destination_id, weight).
    transformation:
        ``"row_standardized"`` (padrão) ou ``"binary"``.
    origin_column:
        Nome da coluna de origem.
    destination_column:
        Nome da coluna de destino.
    weight_column:
        Nome da coluna de peso.
    time_varying:
        Indica se a matriz varia no tempo (um arquivo por período).
    """

    name: str
    path: Path
    transformation: str = "row_standardized"
    origin_column: str = "origin_id"
    destination_column: str = "destination_id"
    weight_column: str = "weight"
    time_varying: bool = False


def _load_csv(path: Path, spec: WeightSpec) -> pd.DataFrame:
    if not path.exists():
        raise PanelError(f"Arquivo de pesos não encontrado: {path}")
    df = pd.read_csv(path)
    for col in (spec.origin_column, spec.destination_column, spec.weight_column):
        if col not in df.columns:
            raise PanelError(f"Coluna de pesos ausente no arquivo {path.name}: {col}")
    return df


def _to_matrix(df: pd.DataFrame, ids: list[str], spec: WeightSpec) -> np.ndarray:
    """Converte lista de arestas em matriz densa n×n."""
    n = len(ids)
    idx_map = {uid: i for i, uid in enumerate(ids)}
    w = np.zeros((n, n), dtype=float)
    for _, row in df.iterrows():
        orig = str(row[spec.origin_column])
        dest = str(row[spec.destination_column])
        if orig not in idx_map or dest not in idx_map:
            continue
        w[idx_map[orig], idx_map[dest]] = float(row[spec.weight_column])

    if spec.transformation == "row_standardized":
        row_sums = w.sum(axis=1, keepdims=True)
        row_sums[row_sums == 0] = 1.0
        w = w / row_sums
    return w


def build_weights(
    spec: WeightSpec,
    ids: list[str],
    period: str | None = None,
) -> np.ndarray:
    """Constrói a matriz de pesos n×n para as unidades *ids*.

    Parameters
    ----------
    spec:
        Especificação da matriz de pesos.
    ids:
        Lista ordenada de identificadores de unidade.
    period:
        Período para matrizes variáveis no tempo (ignorado se ``time_varying=False``).

    Returns
    -------
    np.ndarray
        Matriz (n, n) com pesos.
    """
    if spec.time_varying:
        if period is None:
            raise PanelError("Período obrigatório para matriz variável no tempo.")
        stem = spec.path.stem
        path = spec.path.parent / f"{stem}_{period}{spec.path.suffix}"
    else:
        path = spec.path

    df = _load_csv(path, spec)
    return _to_matrix(df, ids, spec)


def matrix_diagnostics(w: np.ndarray, name: str = "") -> dict:
    """Diagnósticos básicos de uma matriz de pesos.

    Returns
    -------
    dict
        ``name``, ``n``, ``min_neighbors``, ``max_neighbors``,
        ``mean_neighbors``, ``pct_zeros``, ``is_symmetric``,
        ``row_standardized``.
    """
    n = w.shape[0]
    connections = (w > 0).sum(axis=1)
    row_sums = w.sum(axis=1)
    return {
        "name": name,
        "n": n,
        "min_neighbors": int(connections.min()),
        "max_neighbors": int(connections.max()),
        "mean_neighbors": float(connections.mean()),
        "pct_zeros": float((w == 0).sum() / (n * n)),
        "is_symmetric": bool(np.allclose(w, w.T)),
        "row_standardized": bool(np.allclose(row_sums[row_sums > 0], 1.0)),
    }
