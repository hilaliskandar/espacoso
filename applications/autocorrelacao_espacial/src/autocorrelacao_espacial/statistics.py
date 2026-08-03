from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .errors import DataError, WeightsError
from .multiple_testing import benjamini_hochberg
from .weights import WeightMatrix


@dataclass(frozen=True)
class GlobalResult:
    statistic: float
    expected: float
    p_value: float
    permutations: int
    alternative: str
    simulated_mean: float
    simulated_std: float


def _validate(values: np.ndarray, weights: WeightMatrix) -> np.ndarray:
    x = np.asarray(values, dtype=float)
    if x.shape != (weights.n,):
        raise WeightsError("Vetor e matriz de pesos não estão alinhados.")
    if not np.isfinite(x).all():
        raise DataError("A variável contém valores não finitos.")
    if np.isclose(float(np.var(x)), 0.0):
        raise DataError("A variável precisa apresentar variância positiva.")
    if weights.s0 <= 0:
        raise WeightsError("A matriz não possui ligações; S0 é zero.")
    return x


def _pseudo_p(observed: float, simulated: np.ndarray, center: float, alternative: str) -> float:
    if alternative == "greater":
        extreme = simulated >= observed
    elif alternative == "less":
        extreme = simulated <= observed
    elif alternative == "two-sided":
        extreme = np.abs(simulated - center) >= abs(observed - center)
    else:
        raise ValueError(f"Alternativa desconhecida: {alternative}")
    return float((int(np.sum(extreme)) + 1) / (len(simulated) + 1))


def moran_i(values: np.ndarray, weights: WeightMatrix) -> float:
    x = _validate(values, weights)
    z = x - float(x.mean())
    denominator = float(z @ z)
    numerator = float(z @ weights.lag(z))
    return float((weights.n / weights.s0) * numerator / denominator)


def geary_c(values: np.ndarray, weights: WeightMatrix) -> float:
    x = _validate(values, weights)
    z = x - float(x.mean())
    denominator = float(z @ z)
    matrix = weights.dense()
    differences = x[:, None] - x[None, :]
    numerator = float(np.sum(matrix * differences * differences))
    return float(((weights.n - 1) / (2 * weights.s0)) * numerator / denominator)


def permutation_global(
    values: np.ndarray,
    weights: WeightMatrix,
    statistic: str,
    permutations: int,
    seed: int,
    alternative: str,
) -> GlobalResult:
    x = _validate(values, weights)
    if statistic == "moran":
        observed = moran_i(x, weights)
        expected = -1.0 / (weights.n - 1)
        function = moran_i
    elif statistic == "geary":
        observed = geary_c(x, weights)
        expected = 1.0
        function = geary_c
    else:
        raise ValueError("statistic deve ser 'moran' ou 'geary'.")
    rng = np.random.default_rng(seed)
    simulated = np.asarray([function(rng.permutation(x), weights) for _ in range(permutations)], dtype=float)
    return GlobalResult(
        statistic=float(observed),
        expected=float(expected),
        p_value=_pseudo_p(observed, simulated, expected, alternative),
        permutations=permutations,
        alternative=alternative,
        simulated_mean=float(simulated.mean()),
        simulated_std=float(simulated.std(ddof=1)) if permutations > 1 else 0.0,
    )


def local_moran(
    values: np.ndarray,
    weights: WeightMatrix,
    permutations: int,
    seed: int,
    alpha: float,
    fdr: bool,
) -> pd.DataFrame:
    x = _validate(values, weights)
    z = x - float(x.mean())
    m2 = float(np.mean(z * z))
    lag_z = weights.lag(z)
    observed = z * lag_z / m2
    rng = np.random.default_rng(seed)
    simulated = np.zeros((permutations, weights.n), dtype=float)
    all_indices = np.arange(weights.n)
    for i, (nbrs, vals) in enumerate(zip(weights.neighbors, weights.weights, strict=True)):
        if not nbrs:
            simulated[:, i] = np.nan
            continue
        others = all_indices[all_indices != i]
        neighbor_count = len(nbrs)
        weight_values = np.asarray(vals, dtype=float)
        for p in range(permutations):
            sample = rng.permutation(others)[:neighbor_count]
            simulated[p, i] = z[i] * float(weight_values @ z[sample]) / m2
    p_values = np.ones(weights.n, dtype=float)
    for i in range(weights.n):
        if not weights.neighbors[i]:
            continue
        sims = simulated[:, i]
        center = float(np.mean(sims))
        p_values[i] = (int(np.sum(np.abs(sims - center) >= abs(observed[i] - center))) + 1) / (permutations + 1)
    q_values = benjamini_hochberg(p_values)
    significant = q_values <= alpha if fdr else p_values <= alpha
    clusters: list[str] = []
    for i in range(weights.n):
        if not weights.neighbors[i]:
            clusters.append("Island")
        elif not significant[i]:
            clusters.append("NS")
        elif z[i] >= 0 and lag_z[i] >= 0:
            clusters.append("HH")
        elif z[i] < 0 and lag_z[i] < 0:
            clusters.append("LL")
        elif z[i] >= 0 and lag_z[i] < 0:
            clusters.append("HL")
        else:
            clusters.append("LH")
    return pd.DataFrame(
        {
            "id": weights.ids,
            "value": x,
            "z": z,
            "spatial_lag_z": lag_z,
            "local_moran": observed,
            "p_value": p_values,
            "q_value": q_values,
            "significant": significant,
            "cluster": clusters,
            "neighbors": weights.cardinalities,
        }
    )


def getis_ord_g_star(
    values: np.ndarray,
    weights: WeightMatrix,
    permutations: int,
    seed: int,
    alpha: float,
    fdr: bool,
) -> pd.DataFrame:
    x = _validate(values, weights)
    matrix = weights.dense().copy()
    np.fill_diagonal(matrix, 1.0)
    x_bar = float(x.mean())
    s = float(np.sqrt(np.mean(x * x) - x_bar * x_bar))
    if np.isclose(s, 0.0):
        raise DataError("Desvio-padrão nulo para Getis-Ord G*.")
    sum_w = matrix.sum(axis=1)
    sum_w2 = (matrix * matrix).sum(axis=1)
    denominator = s * np.sqrt((weights.n * sum_w2 - sum_w * sum_w) / (weights.n - 1))
    if np.any(np.isclose(denominator, 0.0)):
        raise WeightsError("Getis-Ord G* possui denominador nulo para ao menos uma unidade.")
    observed = (matrix @ x - x_bar * sum_w) / denominator
    rng = np.random.default_rng(seed)
    simulated = np.zeros((permutations, weights.n), dtype=float)
    for p in range(permutations):
        permuted = rng.permutation(x)
        perm_mean = float(permuted.mean())
        simulated[p] = (matrix @ permuted - perm_mean * sum_w) / denominator
    p_values = np.empty(weights.n, dtype=float)
    for i in range(weights.n):
        center = float(simulated[:, i].mean())
        p_values[i] = (int(np.sum(np.abs(simulated[:, i] - center) >= abs(observed[i] - center))) + 1) / (permutations + 1)
    q_values = benjamini_hochberg(p_values)
    significant = q_values <= alpha if fdr else p_values <= alpha
    classification = np.where(~significant, "NS", np.where(observed > 0, "Hot", "Cold"))
    return pd.DataFrame(
        {
            "id": weights.ids,
            "value": x,
            "g_star": observed,
            "p_value": p_values,
            "q_value": q_values,
            "significant": significant,
            "classification": classification,
            "neighbors_with_self": (matrix != 0).sum(axis=1),
        }
    )
