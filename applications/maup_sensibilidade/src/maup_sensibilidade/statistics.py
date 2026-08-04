from __future__ import annotations

"""Estatísticas descritivas e autocorrelação para análise MAUP."""

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .errors import DataError


# ---------------------------------------------------------------------------
# Matriz de contiguidade simples
# ---------------------------------------------------------------------------


def contiguity_matrix(gdf) -> np.ndarray:  # type: ignore[return]
    """Matriz de contiguidade Queen (toque de borda/vértice) normalizada por linha."""
    n = len(gdf)
    w = np.zeros((n, n), dtype=float)
    for i in range(n):
        for j in range(i + 1, n):
            if gdf.geometry.iloc[i].touches(gdf.geometry.iloc[j]) or gdf.geometry.iloc[
                i
            ].intersects(gdf.geometry.iloc[j]):
                if not gdf.geometry.iloc[i].equals(gdf.geometry.iloc[j]):
                    w[i, j] = 1.0
                    w[j, i] = 1.0
    # row-standardise
    row_sums = w.sum(axis=1, keepdims=True)
    row_sums[row_sums == 0] = 1.0
    return w / row_sums


# ---------------------------------------------------------------------------
# Moran I global (permutação)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class MoranResult:
    moran_i: float
    expected: float
    p_value: float
    permutations: int


def moran_i(values: np.ndarray, w: np.ndarray) -> float:
    """I de Moran global."""
    x = np.asarray(values, dtype=float)
    z = x - x.mean()
    s0 = float(w.sum())
    if s0 <= 0.0:
        raise DataError("Matriz de pesos sem ligações (S0 = 0).")
    n = len(x)
    return float((n / s0) * (z @ w @ z) / (z @ z))


def permutation_moran(
    values: np.ndarray,
    w: np.ndarray,
    permutations: int,
    seed: int,
) -> MoranResult:
    """I de Moran com p-valor pseudo-aleatório (two-sided)."""
    x = np.asarray(values, dtype=float)
    if float(np.var(x)) == 0.0:
        raise DataError("Variável sem variância; Moran não pode ser calculado.")
    observed = moran_i(x, w)
    expected = -1.0 / (len(x) - 1)
    rng = np.random.default_rng(seed)
    sim = np.asarray(
        [moran_i(rng.permutation(x), w) for _ in range(permutations)], dtype=float
    )
    extreme = int(np.sum(np.abs(sim - expected) >= abs(observed - expected)))
    p_value = (extreme + 1) / (permutations + 1)
    return MoranResult(
        moran_i=observed,
        expected=expected,
        p_value=float(p_value),
        permutations=permutations,
    )


# ---------------------------------------------------------------------------
# Estatísticas descritivas
# ---------------------------------------------------------------------------


def descriptive_stats(
    aggregated_frames: dict[str, pd.DataFrame],
    variables: tuple[str, ...],
) -> pd.DataFrame:
    """Tabela comparativa de estatísticas descritivas entre esquemas."""
    rows: list[dict] = []
    for scheme_name, agg in aggregated_frames.items():
        for var in variables:
            col = f"{var}_mean"
            if col not in agg.columns:
                continue
            vals = agg[col].dropna()
            rows.append(
                {
                    "scheme": scheme_name,
                    "variable": var,
                    "n": len(vals),
                    "mean": float(vals.mean()),
                    "std": float(vals.std(ddof=1)) if len(vals) > 1 else 0.0,
                    "min": float(vals.min()),
                    "p25": float(vals.quantile(0.25)),
                    "median": float(vals.median()),
                    "p75": float(vals.quantile(0.75)),
                    "max": float(vals.max()),
                }
            )
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Tabela de estabilidade de sinais, magnitudes e significância
# ---------------------------------------------------------------------------


def stability_table(
    moran_results: dict[str, dict[str, MoranResult]],
) -> pd.DataFrame:
    """Tabela de estabilidade do I de Moran entre esquemas.

    Parameters
    ----------
    moran_results:
        Dict[variable -> Dict[scheme -> MoranResult]]
    """
    rows: list[dict] = []
    for variable, by_scheme in moran_results.items():
        values = [r.moran_i for r in by_scheme.values()]
        p_values = [r.p_value for r in by_scheme.values()]
        for scheme, result in by_scheme.items():
            rows.append(
                {
                    "variable": variable,
                    "scheme": scheme,
                    "moran_i": result.moran_i,
                    "expected": result.expected,
                    "p_value": result.p_value,
                    "significant": result.p_value <= 0.05,
                    "sign_positive": result.moran_i > 0,
                }
            )
        # estabilidade: desvio-padrão dos I entre esquemas
        rows_var = [r for r in rows if r["variable"] == variable]
        std_i = float(np.std([r["moran_i"] for r in rows_var], ddof=0))
        range_i = float(max(values) - min(values))
        sign_stable = len(set(r["sign_positive"] for r in rows_var)) == 1
        sig_stable = len(set(r["significant"] for r in rows_var)) == 1
        for r in rows_var:
            r["std_i_across_schemes"] = std_i
            r["range_i_across_schemes"] = range_i
            r["sign_stable"] = sign_stable
            r["significance_stable"] = sig_stable
    return pd.DataFrame(rows)
