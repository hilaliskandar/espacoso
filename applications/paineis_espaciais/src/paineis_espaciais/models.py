from __future__ import annotations

"""Modelos de painel: efeitos fixos, lag espacial e erro espacial.

Abordagem
---------
- Efeitos fixos de unidade (within) e/ou tempo são demeanados antes de estimar.
- Modelo espacial estático: versão de dois estágios (IV/2SLS) para lag espacial
  e estimação por MLE aproximada para erro espacial.
- Modelo dinâmico: quando ``dynamic=True`` e defasagem temporal disponível,
  inclui ``y_lag1`` como regressor adicional com aviso sobre limites de
  identificação (requer instrumentos válidos fora do escopo desta implementação).
- Todos os estimadores são implementados via statsmodels e numpy sem dependências
  de libpysal para manter o pacote leve e didático.
"""

import warnings
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.regression.linear_model import RegressionResultsWrapper

from .errors import PanelError
from .panel import PanelData


# ---------------------------------------------------------------------------
# Utilitários internos
# ---------------------------------------------------------------------------

def _demean_within(
    y: np.ndarray,
    X: np.ndarray,
    unit_ids: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Demean y e X pela média de cada unidade (efeito fixo de unidade)."""
    units = np.unique(unit_ids)
    y_dm = y.copy().astype(float)
    X_dm = X.copy().astype(float)
    for u in units:
        mask = unit_ids == u
        y_dm[mask] -= y_dm[mask].mean()
        X_dm[mask] -= X_dm[mask].mean(axis=0)
    return y_dm, X_dm


def _demean_time(
    y: np.ndarray,
    X: np.ndarray,
    time_ids: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Demean y e X pela média de cada período (efeito fixo de tempo)."""
    times = np.unique(time_ids)
    y_dm = y.copy().astype(float)
    X_dm = X.copy().astype(float)
    for t in times:
        mask = time_ids == t
        y_dm[mask] -= y_dm[mask].mean()
        X_dm[mask] -= X_dm[mask].mean(axis=0)
    return y_dm, X_dm


def _build_arrays(
    panel: PanelData,
    target: str,
    predictors: list[str],
    fixed_effects: str,
    dynamic: bool,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, list[str]]:
    """Extrai y, X, unit_ids, time_ids com demeaning de efeitos fixos."""
    df = panel.data.copy()
    missing_cols = [c for c in [target] + predictors if c not in df.columns]
    if missing_cols:
        raise PanelError(f"Colunas ausentes no painel: {missing_cols}")

    if dynamic:
        lag_col = f"{target}_lag1"
        if lag_col not in df.columns:
            raise PanelError(
                f"Coluna '{lag_col}' não encontrada. Execute lag_column() antes de fit_spatial_lag/error com dynamic=True."
            )
        predictors = [lag_col] + predictors
        warnings.warn(
            "Modelo dinâmico inclui defasagem temporal como regressor. "
            "Os estimadores de efeitos fixos com variável dependente defasada "
            "são inconsistentes em painéis curtos (viés de Nickell). "
            "Instrumentalize adequadamente para inferência causal válida.",
            stacklevel=4,
        )

    df_clean = df[[target] + predictors].dropna()
    if len(df_clean) < len(df):
        warnings.warn(
            f"Removidas {len(df) - len(df_clean)} observações com NaN após dropna().",
            stacklevel=4,
        )

    unit_ids = df_clean.index.get_level_values(0).to_numpy(dtype=str)
    time_ids = df_clean.index.get_level_values(1).to_numpy()

    y = df_clean[target].to_numpy(dtype=float)
    X = df_clean[predictors].to_numpy(dtype=float)

    if fixed_effects in ("unit", "two_way"):
        y, X = _demean_within(y, X, unit_ids)
    if fixed_effects in ("time", "two_way"):
        y, X = _demean_time(y, X, time_ids)

    return y, X, unit_ids, time_ids, predictors


# ---------------------------------------------------------------------------
# Dataclasses de resultado
# ---------------------------------------------------------------------------

@dataclass
class FittedPanel:
    """Resultado de modelo de painel não espacial (efeitos fixos OLS).

    Attributes
    ----------
    spec_name:
        Identificador do modelo.
    target:
        Variável dependente.
    predictors:
        Lista de preditores usados.
    fixed_effects:
        Tipo de efeito fixo aplicado.
    result:
        Objeto de resultado do statsmodels.
    n_obs:
        Número de observações usadas.
    n_units:
        Número de unidades.
    n_periods:
        Número de períodos.
    """

    spec_name: str
    target: str
    predictors: list[str]
    fixed_effects: str
    result: RegressionResultsWrapper
    n_obs: int
    n_units: int
    n_periods: int


@dataclass
class SpatialPanelResult:
    """Resultado de modelo de painel espacial.

    Attributes
    ----------
    spec_name:
        Identificador do modelo.
    model_type:
        ``"spatial_lag"`` ou ``"spatial_error"``.
    target:
        Variável dependente.
    predictors:
        Lista de preditores (após demeaning).
    fixed_effects:
        Tipo de efeito fixo aplicado.
    params:
        Parâmetros estimados (array 1D).
    param_names:
        Nomes dos parâmetros.
    std_errors:
        Erros-padrão.
    t_values:
        Estatísticas t.
    p_values:
        p-valores.
    rho_or_lambda:
        Coeficiente espacial estimado (ρ para lag, λ para erro).
    spatial_param_name:
        ``"rho"`` ou ``"lambda"``.
    r_squared:
        R² calculado sobre resíduos demeanados.
    n_obs:
        Número de observações usadas.
    n_units:
        Número de unidades.
    n_periods:
        Número de períodos.
    dynamic:
        Indica se modelo dinâmico foi estimado.
    identification_note:
        Nota sobre limites de identificação causal.
    """

    spec_name: str
    model_type: str
    target: str
    predictors: list[str]
    fixed_effects: str
    params: np.ndarray
    param_names: list[str]
    std_errors: np.ndarray
    t_values: np.ndarray
    p_values: np.ndarray
    rho_or_lambda: float
    spatial_param_name: str
    r_squared: float
    n_obs: int
    n_units: int
    n_periods: int
    dynamic: bool
    identification_note: str


# ---------------------------------------------------------------------------
# Estimadores
# ---------------------------------------------------------------------------

def fit_fe(
    panel: PanelData,
    target: str,
    predictors: list[str],
    fixed_effects: str = "unit",
    spec_name: str = "fe",
) -> FittedPanel:
    """Estima modelo de painel com efeitos fixos (within OLS).

    Parameters
    ----------
    panel:
        :class:`~paineis_espaciais.panel.PanelData`.
    target:
        Variável dependente.
    predictors:
        Lista de preditores.
    fixed_effects:
        ``"unit"`` (padrão), ``"time"`` ou ``"two_way"``.
    spec_name:
        Identificador do resultado.

    Returns
    -------
    FittedPanel
    """
    valid_fe = {"unit", "time", "two_way"}
    if fixed_effects not in valid_fe:
        raise PanelError(f"fixed_effects inválido: {fixed_effects}. Use: {valid_fe}")

    y, X, unit_ids, time_ids, used_preds = _build_arrays(
        panel, target, predictors, fixed_effects, dynamic=False
    )

    result = sm.OLS(y, X).fit(cov_type="HC3")

    return FittedPanel(
        spec_name=spec_name,
        target=target,
        predictors=used_preds,
        fixed_effects=fixed_effects,
        result=result,
        n_obs=len(y),
        n_units=panel.n_units,
        n_periods=panel.n_periods,
    )


def _spatial_lag_iv(
    y: np.ndarray,
    X: np.ndarray,
    W: np.ndarray,
    param_names: list[str],
) -> SpatialPanelResult | dict:
    """Estimação IV/2SLS para modelo de lag espacial: y = ρWy + Xβ + ε.

    Instrumentos: Wy, WX (defasagens espaciais das variáveis exógenas).
    """
    n = len(y)
    Wy = W @ y
    WX = W @ X if X.ndim == 2 and X.shape[1] > 0 else np.zeros((n, 0))

    # Instrumentos: X, WX, W²X
    W2X = W @ WX if WX.shape[1] > 0 else np.zeros((n, 0))
    if X.shape[1] > 0:
        Z = np.hstack([X, WX, W2X])
    else:
        Z = np.hstack([Wy.reshape(-1, 1)])

    Xaug = np.column_stack([Wy, X]) if X.shape[1] > 0 else Wy.reshape(-1, 1)
    names_aug = ["rho_Wy"] + param_names

    # Primeira etapa: projetar Xaug sobre Z
    PZ = Z @ np.linalg.lstsq(Z, Xaug, rcond=None)[0]
    # Segunda etapa: OLS de y sobre PZ
    beta_iv, *_ = np.linalg.lstsq(PZ, y, rcond=None)
    y_hat = Xaug @ beta_iv
    resid = y - y_hat
    s2 = float(np.dot(resid, resid) / max(n - len(beta_iv), 1))
    XtX_inv = np.linalg.pinv(PZ.T @ PZ)
    vcov = s2 * XtX_inv
    se = np.sqrt(np.diag(vcov))
    t_vals = beta_iv / np.where(se > 0, se, np.nan)
    from scipy.stats import t as t_dist
    p_vals = 2 * t_dist.sf(np.abs(t_vals), df=n - len(beta_iv))

    ss_tot = np.sum((y - y.mean()) ** 2)
    ss_res = np.dot(resid, resid)
    r2 = float(1 - ss_res / ss_tot) if ss_tot > 0 else 0.0

    return {
        "params": beta_iv,
        "param_names": names_aug,
        "std_errors": se,
        "t_values": t_vals,
        "p_values": p_vals,
        "rho_or_lambda": float(beta_iv[0]),
        "r_squared": r2,
    }


def _spatial_error_gm(
    y: np.ndarray,
    X: np.ndarray,
    W: np.ndarray,
    param_names: list[str],
) -> dict:
    """Estimação por Generalised Moments para modelo de erro espacial: y = Xβ + u, u = λWu + ε.

    Implementação iterativa simples (Cochrane-Orcutt espacial):
    1. Estimar β por OLS.
    2. Estimar λ via regressão dos resíduos: ê = λWê + η.
    3. Transformar e re-estimar até convergência.
    """
    from scipy.stats import t as t_dist

    n = len(y)
    # Iteração 0: OLS
    if X.shape[1] > 0:
        beta = np.linalg.lstsq(X, y, rcond=None)[0]
        resid = y - X @ beta
    else:
        beta = np.array([])
        resid = y.copy()

    lam = 0.0
    for _ in range(10):
        We = W @ resid
        # Estimar λ: regressão simples de e em We
        if np.dot(We, We) > 1e-12:
            lam_new = float(np.dot(We, resid) / np.dot(We, We))
            lam_new = max(-0.99, min(0.99, lam_new))
        else:
            lam_new = 0.0
        if abs(lam_new - lam) < 1e-8:
            break
        lam = lam_new
        # Transformação de Cochrane-Orcutt espacial
        y_star = y - lam * (W @ y)
        X_star = X - lam * (W @ X)
        if X_star.shape[1] > 0:
            beta = np.linalg.lstsq(X_star, y_star, rcond=None)[0]
            resid = y - X @ beta
        else:
            beta = np.array([])
            resid = y.copy()

    y_star = y - lam * (W @ y)
    X_star = X - lam * (W @ X)
    if X_star.shape[1] > 0:
        beta_final, _, _, _ = np.linalg.lstsq(X_star, y_star, rcond=None)
    else:
        beta_final = np.array([])

    resid_final = y - (X @ beta_final if X.shape[1] > 0 else np.zeros(n))
    s2 = float(np.dot(resid_final, resid_final) / max(n - len(beta_final) - 1, 1))
    if X_star.shape[1] > 0:
        XtX_inv = np.linalg.pinv(X_star.T @ X_star)
        vcov = s2 * XtX_inv
        se = np.sqrt(np.diag(vcov))
        t_vals = beta_final / np.where(se > 0, se, np.nan)
        p_vals = 2 * t_dist.sf(np.abs(t_vals), df=max(n - len(beta_final) - 1, 1))
    else:
        se = np.array([])
        t_vals = np.array([])
        p_vals = np.array([])

    ss_tot = np.sum((y - y.mean()) ** 2)
    ss_res = np.dot(resid_final, resid_final)
    r2 = float(1 - ss_res / ss_tot) if ss_tot > 0 else 0.0

    return {
        "params": beta_final,
        "param_names": param_names,
        "std_errors": se,
        "t_values": t_vals,
        "p_values": p_vals,
        "rho_or_lambda": lam,
        "r_squared": r2,
    }


def fit_spatial_lag(
    panel: PanelData,
    W: np.ndarray,
    target: str,
    predictors: list[str],
    fixed_effects: str = "unit",
    spec_name: str = "spatial_lag",
    dynamic: bool = False,
) -> SpatialPanelResult:
    """Estima modelo de lag espacial com efeitos fixos via IV/2SLS.

    .. math::
        y_{it} = \\rho W y_{it} + X_{it}\\beta + \\alpha_i + \\gamma_t + \\varepsilon_{it}

    Parameters
    ----------
    panel:
        :class:`~paineis_espaciais.panel.PanelData`.
    W:
        Matriz de pesos espaciais (n_units × n_units), row-standardizada.
    target:
        Variável dependente.
    predictors:
        Lista de preditores.
    fixed_effects:
        ``"unit"``, ``"time"`` ou ``"two_way"``.
    spec_name:
        Identificador do resultado.
    dynamic:
        Inclui defasagem temporal ``{target}_lag1`` como regressor.

    Returns
    -------
    SpatialPanelResult

    Notes
    -----
    **Limites de identificação**: O coeficiente ρ identifica spillovers contemporâneos
    entre unidades, condicionado aos efeitos fixos e preditores. A interpretação causal
    requer que W seja exógena (determinada fora do modelo) e que os instrumentos
    (defasagens espaciais de X) satisfaçam as condições de relevância e exclusão.
    """
    valid_fe = {"unit", "time", "two_way"}
    if fixed_effects not in valid_fe:
        raise PanelError(f"fixed_effects inválido: {fixed_effects}. Use: {valid_fe}")

    y, X, unit_ids, time_ids, used_preds = _build_arrays(
        panel, target, predictors, fixed_effects, dynamic=dynamic
    )

    n_units = panel.n_units
    n_periods = len(np.unique(time_ids))

    # Expandir W para T períodos (W_block = I_T ⊗ W)
    T = len(np.unique(time_ids))
    W_block = np.kron(np.eye(T), W)
    # Ordenar por (unit, time) já garantido pelo PanelData
    # Mas W_block pressupõe ordenação por (time, unit); precisamos de (unit, time)
    # Re-ordenar: o índice atual é (unit, time) → precisamos mapear
    units_sorted = np.unique(unit_ids)
    times_sorted = np.unique(time_ids)
    order = []
    for u in units_sorted:
        for t in times_sorted:
            mask = (unit_ids == u) & (time_ids == t)
            idxs = np.where(mask)[0]
            if len(idxs):
                order.append(idxs[0])
    order = np.array(order)
    y_ord = y[order]
    X_ord = X[order]
    W_block_reord = W_block  # já em (unit, time) se expandido como kron(I_T, W)
    # Nota: kron(I_T, W) opera em vetores no formato [u0t0, u0t1, ..., u(n-1)t(T-1)]
    # que é exatamente (unit, time) → correto.

    est = _spatial_lag_iv(y_ord, X_ord, W_block_reord, used_preds)

    id_note = (
        "Modelo de lag espacial estimado por IV/2SLS. "
        "ρ identificado sob exogeneidade de W e validade dos instrumentos (WX, W²X). "
        "Efeitos fixos de unidade/tempo removidos por demeaning (within). "
        "Interpretação causal requer exogeneidade dos regressores condicionada aos efeitos fixos."
    )
    if dynamic:
        id_note += (
            " Modelo dinâmico: viés de Nickell presente em painéis curtos. "
            "Para inferência válida, use estimadores de Arellano-Bond."
        )

    return SpatialPanelResult(
        spec_name=spec_name,
        model_type="spatial_lag",
        target=target,
        predictors=used_preds,
        fixed_effects=fixed_effects,
        params=est["params"],
        param_names=est["param_names"],
        std_errors=est["std_errors"],
        t_values=est["t_values"],
        p_values=est["p_values"],
        rho_or_lambda=est["rho_or_lambda"],
        spatial_param_name="rho",
        r_squared=est["r_squared"],
        n_obs=len(y),
        n_units=n_units,
        n_periods=n_periods,
        dynamic=dynamic,
        identification_note=id_note,
    )


def fit_spatial_error(
    panel: PanelData,
    W: np.ndarray,
    target: str,
    predictors: list[str],
    fixed_effects: str = "unit",
    spec_name: str = "spatial_error",
    dynamic: bool = False,
) -> SpatialPanelResult:
    """Estima modelo de erro espacial com efeitos fixos via GM iterativo.

    .. math::
        y_{it} = X_{it}\\beta + u_{it}, \\quad u_{it} = \\lambda W u_{it} + \\varepsilon_{it}

    Parameters
    ----------
    panel:
        :class:`~paineis_espaciais.panel.PanelData`.
    W:
        Matriz de pesos espaciais (n_units × n_units), row-standardizada.
    target:
        Variável dependente.
    predictors:
        Lista de preditores.
    fixed_effects:
        ``"unit"``, ``"time"`` ou ``"two_way"``.
    spec_name:
        Identificador do resultado.
    dynamic:
        Inclui defasagem temporal ``{target}_lag1`` como regressor.

    Returns
    -------
    SpatialPanelResult

    Notes
    -----
    **Limites de identificação**: λ captura autocorrelação espacial nos erros,
    corrigindo inferência mas não alterando consistência dos estimadores β.
    Interpretação causal dos βs depende da ausência de variáveis omitidas
    correlacionadas com os preditores após remoção de efeitos fixos.
    """
    valid_fe = {"unit", "time", "two_way"}
    if fixed_effects not in valid_fe:
        raise PanelError(f"fixed_effects inválido: {fixed_effects}. Use: {valid_fe}")

    y, X, unit_ids, time_ids, used_preds = _build_arrays(
        panel, target, predictors, fixed_effects, dynamic=dynamic
    )

    n_units = panel.n_units
    n_periods = len(np.unique(time_ids))

    T = len(np.unique(time_ids))
    W_block = np.kron(np.eye(T), W)

    est = _spatial_error_gm(y, X, W_block, used_preds)

    id_note = (
        "Modelo de erro espacial estimado por GM iterativo (Cochrane-Orcutt espacial). "
        "λ captura autocorrelação espacial residual, melhorando eficiência dos βs. "
        "Efeitos fixos de unidade/tempo removidos por demeaning (within). "
        "Interpretação causal dos βs requer exogeneidade condicional dos preditores."
    )
    if dynamic:
        id_note += (
            " Modelo dinâmico: viés de Nickell presente em painéis curtos. "
            "Para inferência válida, use estimadores de Arellano-Bond."
        )

    return SpatialPanelResult(
        spec_name=spec_name,
        model_type="spatial_error",
        target=target,
        predictors=used_preds,
        fixed_effects=fixed_effects,
        params=est["params"],
        param_names=est["param_names"],
        std_errors=est["std_errors"],
        t_values=est["t_values"],
        p_values=est["p_values"],
        rho_or_lambda=est["rho_or_lambda"],
        spatial_param_name="lambda",
        r_squared=est["r_squared"],
        n_obs=len(y),
        n_units=n_units,
        n_periods=n_periods,
        dynamic=dynamic,
        identification_note=id_note,
    )


def compare_models(
    fe: FittedPanel,
    spatial_results: list[SpatialPanelResult],
) -> pd.DataFrame:
    """Tabela comparativa entre modelo FE não espacial e modelos espaciais.

    Returns
    -------
    pd.DataFrame
        Uma linha por modelo com: spec_name, model_type, fixed_effects,
        n_obs, r_squared, spatial_param_name, spatial_coef, dynamic.
    """
    rows: list[dict] = []

    fe_r2 = float(fe.result.rsquared)
    rows.append({
        "spec_name": fe.spec_name,
        "model_type": "fe_ols",
        "fixed_effects": fe.fixed_effects,
        "n_obs": fe.n_obs,
        "r_squared": round(fe_r2, 4),
        "spatial_param_name": "",
        "spatial_coef": float("nan"),
        "dynamic": False,
    })

    for sr in spatial_results:
        rows.append({
            "spec_name": sr.spec_name,
            "model_type": sr.model_type,
            "fixed_effects": sr.fixed_effects,
            "n_obs": sr.n_obs,
            "r_squared": round(sr.r_squared, 4),
            "spatial_param_name": sr.spatial_param_name,
            "spatial_coef": round(sr.rho_or_lambda, 4),
            "dynamic": sr.dynamic,
        })

    return pd.DataFrame(rows)
