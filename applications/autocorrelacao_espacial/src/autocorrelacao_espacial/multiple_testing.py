from __future__ import annotations

import numpy as np


def benjamini_hochberg(p_values: np.ndarray) -> np.ndarray:
    p = np.asarray(p_values, dtype=float)
    if p.ndim != 1:
        raise ValueError("p_values deve ser unidimensional.")
    if np.any((p < 0) | (p > 1) | ~np.isfinite(p)):
        raise ValueError("p_values deve conter valores finitos entre 0 e 1.")
    n = len(p)
    if n == 0:
        return p.copy()
    order = np.argsort(p, kind="stable")
    ranked = p[order]
    adjusted = ranked * n / np.arange(1, n + 1)
    adjusted = np.minimum.accumulate(adjusted[::-1])[::-1]
    adjusted = np.clip(adjusted, 0.0, 1.0)
    result = np.empty_like(adjusted)
    result[order] = adjusted
    return result
