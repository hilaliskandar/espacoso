"""Carregamento e transformação de matrizes de pesos espaciais."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy import sparse

from .config import WeightSpec
from .errors import WeightsError


@dataclass(frozen=True)
class WeightMatrix:
    name: str
    ids: tuple[str, ...]
    matrix: sparse.csr_matrix
    islands: tuple[str, ...]
    transformation: str

    @property
    def n(self) -> int:
        return self.matrix.shape[0]

    @property
    def s0(self) -> float:
        return float(self.matrix.sum())

    def to_dense(self) -> np.ndarray:
        return self.matrix.toarray()


def load_weights(spec: WeightSpec, ids: list[str]) -> WeightMatrix:
    if not spec.path.exists():
        raise WeightsError(f"Arquivo de pesos não encontrado: {spec.path}")
    edges = pd.read_csv(spec.path)
    required = {spec.origin_column, spec.destination_column, spec.weight_column}
    missing = required.difference(edges.columns)
    if missing:
        raise WeightsError(f"Colunas ausentes no arquivo de pesos: {sorted(missing)}")

    ordered_ids = [str(x).strip() for x in ids]
    if len(ordered_ids) != len(set(ordered_ids)):
        raise WeightsError("A ordem de observações contém identificadores duplicados.")
    index = {value: i for i, value in enumerate(ordered_ids)}

    origin = edges[spec.origin_column].astype(str).str.strip()
    destination = edges[spec.destination_column].astype(str).str.strip()
    unknown = sorted((set(origin) | set(destination)).difference(index))
    if unknown:
        raise WeightsError(f"A matriz contém identificadores ausentes nos dados: {unknown[:5]}")
    values = pd.to_numeric(edges[spec.weight_column], errors="coerce")
    if values.isna().any() or not np.isfinite(values.to_numpy()).all():
        raise WeightsError("A matriz contém pesos não numéricos ou não finitos.")
    if (values < 0).any():
        raise WeightsError("Pesos negativos não são aceitos nesta aplicação.")

    rows = origin.map(index).to_numpy(dtype=int)
    cols = destination.map(index).to_numpy(dtype=int)
    mask = rows != cols
    matrix = sparse.coo_matrix(
        (values.to_numpy(dtype=float)[mask], (rows[mask], cols[mask])),
        shape=(len(ordered_ids), len(ordered_ids)),
    ).tocsr()
    matrix.sum_duplicates()
    matrix.eliminate_zeros()

    if spec.transformation == "binary":
        matrix.data[:] = 1.0
    else:
        row_sums = np.asarray(matrix.sum(axis=1)).ravel()
        nonzero = row_sums > 0
        inv = np.zeros_like(row_sums, dtype=float)
        inv[nonzero] = 1.0 / row_sums[nonzero]
        matrix = sparse.diags(inv) @ matrix
        matrix = matrix.tocsr()

    row_sums = np.asarray(matrix.sum(axis=1)).ravel()
    islands = tuple(ordered_ids[i] for i in np.flatnonzero(row_sums == 0))
    return WeightMatrix(
        name=spec.name,
        ids=tuple(ordered_ids),
        matrix=matrix,
        islands=islands,
        transformation=spec.transformation,
    )


def matrix_diagnostics(weights: WeightMatrix) -> dict[str, float | int | str]:
    cardinality = np.diff(weights.matrix.indptr)
    return {
        "weights": weights.name,
        "n": weights.n,
        "s0": weights.s0,
        "islands": len(weights.islands),
        "min_neighbors": int(cardinality.min()) if len(cardinality) else 0,
        "mean_neighbors": float(cardinality.mean()),
        "max_neighbors": int(cardinality.max()) if len(cardinality) else 0,
        "transformation": weights.transformation,
    }
