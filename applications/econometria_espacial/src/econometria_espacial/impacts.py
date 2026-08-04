"""Decomposição de impactos espaciais para SAR e SDM.

Para SAR:
    impacto_total = (I - ρW)⁻¹ β_k
    impacto_direto = média da diagonal de (I - ρW)⁻¹ β_k
    impacto_indireto = impacto_total - impacto_direto

Para SDM:
    impacto_total = (I - ρW)⁻¹ (β_k + θ_k W)  →  média das linhas de S(W)
    S(W) = (I - ρW)⁻¹ (β_k I + θ_k W)

Referência: LeSage & Pace (2009), cap. 2.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .models import SpatialModelResult


@dataclass(frozen=True)
class ImpactDecomposition:
    """Decomposição de impactos para um preditor."""
    model: str
    term: str
    direct: float
    indirect: float
    total: float


def _spatial_multiplier(rho: float, w: np.ndarray) -> np.ndarray:
    """(I - ρW)⁻¹ usando inversão direta (eficiente para n pequeno/médio)."""
    n = w.shape[0]
    return np.linalg.inv(np.eye(n) - rho * w)


def compute_impacts(result: SpatialModelResult) -> list[ImpactDecomposition]:
    """Calcula decomposição de impactos diretos, indiretos e totais.

    Para OLS e SLX: impacto direto = coeficiente, indireto = 0 (sem feedback).
    Para SEM: coeficiente é interpretado como marginal local, sem efeitos indiretos
              transmitidos via y; registramos direto = coef, indireto = 0.
    Para SAR: aplica fórmula de LeSage & Pace.
    Para SDM: aplica fórmula completa com θ.
    """
    model_type = result.model_type
    params = result.params
    w = result.w
    spec = result.spec

    # Preditores originais (excluindo constante)
    base_preds = [p for p in spec.predictors]
    # Para SLX/SDM, recupera nomes dos lags
    lag_names = result.lag_feature_names  # e.g. ["W.x1", "W.x2"]

    decomps: list[ImpactDecomposition] = []

    if model_type in {"OLS", "SEM", "SLX"}:
        for pred in base_preds:
            beta = params.get(pred, 0.0)
            decomps.append(ImpactDecomposition(
                model=result.spec.name,
                term=pred,
                direct=float(beta),
                indirect=0.0,
                total=float(beta),
            ))
        # Para SLX: efeito indireto = coeficiente do lag
        if model_type == "SLX":
            # Recalcula: direto=β, indireto=θ (interpretação LeSage & Pace SLX)
            decomps = []
            for pred in base_preds:
                beta = params.get(pred, 0.0)
                theta_name = f"W.{pred}"
                theta = params.get(theta_name, 0.0)
                decomps.append(ImpactDecomposition(
                    model=result.spec.name,
                    term=pred,
                    direct=float(beta),
                    indirect=float(theta),
                    total=float(beta + theta),
                ))
        return decomps

    if model_type == "SAR":
        rho = result.rho
        if rho is None:
            return decomps
        s = _spatial_multiplier(rho, w)
        for pred in base_preds:
            beta_k = params.get(pred, 0.0)
            s_matrix = s * beta_k        # scalar multiplication
            direct = float(np.mean(np.diag(s_matrix)))
            total = float(np.mean(s_matrix.sum(axis=1)))
            indirect = total - direct
            decomps.append(ImpactDecomposition(
                model=result.spec.name,
                term=pred,
                direct=direct,
                indirect=indirect,
                total=total,
            ))
        return decomps

    if model_type == "SDM":
        rho = result.rho
        if rho is None:
            return decomps
        s_inv = _spatial_multiplier(rho, w)
        n = w.shape[0]
        for pred in base_preds:
            beta_k = params.get(pred, 0.0)
            theta_name = f"W.{pred}"
            theta_k = params.get(theta_name, 0.0)
            # S(W) = (I-ρW)⁻¹ (β_k I + θ_k W)
            s_matrix = s_inv @ (beta_k * np.eye(n) + theta_k * w)
            direct = float(np.mean(np.diag(s_matrix)))
            total = float(np.mean(s_matrix.sum(axis=1)))
            indirect = total - direct
            decomps.append(ImpactDecomposition(
                model=result.spec.name,
                term=pred,
                direct=direct,
                indirect=indirect,
                total=total,
            ))
        return decomps

    return decomps


def impacts_table(results: list[SpatialModelResult]) -> pd.DataFrame:
    """Consolida decomposições de múltiplos modelos em um DataFrame."""
    rows: list[dict] = []
    for result in results:
        for imp in compute_impacts(result):
            rows.append({
                "model": imp.model,
                "model_type": result.model_type,
                "term": imp.term,
                "direct": imp.direct,
                "indirect": imp.indirect,
                "total": imp.total,
            })
    return pd.DataFrame(rows)
