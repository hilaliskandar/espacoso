"""Funções de impedância e cálculo de acessibilidade."""
from __future__ import annotations

import math

import numpy as np
import pandas as pd

from .config import ImpedanceSpec


# ---------------------------------------------------------------------------
# Funções de impedância
# ---------------------------------------------------------------------------

def impedance_linear(cost: float, cutoff: float) -> float:
    """
    Decaimento linear: f(c) = max(0, 1 - c/cutoff).

    Decai linearmente de 1 (custo=0) até 0 (custo=cutoff).
    """
    if cutoff <= 0:
        raise ValueError("cutoff deve ser positivo.")
    return max(0.0, 1.0 - cost / cutoff)


def impedance_negative_exponential(cost: float, beta: float) -> float:
    """
    Decaimento exponencial negativo: f(c) = exp(-beta * c).

    Valores maiores de beta produzem decaimento mais rápido.
    """
    if beta <= 0:
        raise ValueError("beta deve ser positivo.")
    return math.exp(-beta * cost)


def impedance_binary(cost: float, cutoff: float) -> float:
    """
    Impedância binária: f(c) = 1 se c <= cutoff, 0 caso contrário.
    """
    if cutoff <= 0:
        raise ValueError("cutoff deve ser positivo.")
    return 1.0 if cost <= cutoff else 0.0


def impedance_power(cost: float, power: float) -> float:
    """
    Decaimento por potência: f(c) = 1 / (1 + c)^power.
    """
    if power <= 0:
        raise ValueError("power deve ser positivo.")
    return 1.0 / (1.0 + cost) ** power


def apply_impedance(cost: float, spec: ImpedanceSpec) -> float:
    """Aplica a função de impedância conforme a especificação."""
    if spec.function == "linear":
        cutoff = spec.cutoff if spec.cutoff is not None else float("inf")
        return impedance_linear(cost, cutoff)
    elif spec.function == "negative_exponential":
        return impedance_negative_exponential(cost, spec.beta)  # type: ignore[arg-type]
    elif spec.function == "binary":
        cutoff = spec.cutoff if spec.cutoff is not None else float("inf")
        return impedance_binary(cost, cutoff)
    elif spec.function == "power":
        return impedance_power(cost, spec.power)  # type: ignore[arg-type]
    else:
        raise ValueError(f"Função de impedância desconhecida: {spec.function!r}.")


# ---------------------------------------------------------------------------
# Cálculo de acessibilidade gravitacional
# ---------------------------------------------------------------------------

def compute_accessibility(
    origin_nodes: dict[int, int],
    destinations: pd.DataFrame,
    destination_node_col: str,
    opportunities_col: str,
    all_distances: dict[int, dict[int, float]],
    spec: ImpedanceSpec,
) -> pd.Series:
    """
    Calcula acessibilidade gravitacional para cada origem.

    A_i = sum_j ( O_j * f(c_ij) )

    onde O_j são as oportunidades no destino j e f é a função de impedância.

    Parâmetros
    ----------
    origin_nodes:
        {índice_origem: node_id} — nó da rede ao qual cada origem está atribuída.
    destinations:
        DataFrame com colunas [destination_node_col, opportunities_col].
    destination_node_col:
        Nome da coluna com o node_id dos destinos.
    opportunities_col:
        Nome da coluna com o número de oportunidades em cada destino.
    all_distances:
        {node_id_origem: {node_id_destino: custo}}.
    spec:
        Especificação da função de impedância.

    Retorna
    -------
    pd.Series com índice igual ao índice de origin_nodes e valores de acessibilidade.
    """
    results: dict[int, float] = {}
    for origin_idx, origin_node in origin_nodes.items():
        dist_from_origin = all_distances.get(origin_node, {})
        acc = 0.0
        for _, dest_row in destinations.iterrows():
            dest_node = int(dest_row[destination_node_col])
            opps = float(dest_row[opportunities_col])
            if opps <= 0:
                continue
            cost = dist_from_origin.get(dest_node, float("inf"))
            acc += opps * apply_impedance(cost, spec)
        results[origin_idx] = acc
    return pd.Series(results)


def compute_euclidean_distances(
    origins: "gpd.GeoDataFrame",  # noqa: F821
    origins_id_col: str,
) -> pd.DataFrame:
    """
    Calcula distâncias euclidianas entre todos os pares de origens.

    Retorna DataFrame com colunas [origin, destination, euclidean_m].
    """
    rows = []
    indices = list(origins.index)
    centroids = {idx: origins.loc[idx, "geometry"].centroid for idx in indices}
    for i, a in enumerate(indices):
        for b in indices[i + 1 :]:
            ca = centroids[a]
            cb = centroids[b]
            dist = math.sqrt((ca.x - cb.x) ** 2 + (ca.y - cb.y) ** 2)
            rows.append({
                "origin": origins.loc[a, origins_id_col],
                "destination": origins.loc[b, origins_id_col],
                "euclidean_m": round(dist, 2),
            })
    return pd.DataFrame(rows)


def compare_network_vs_euclidean(
    origins: "gpd.GeoDataFrame",  # noqa: F821
    origins_id_col: str,
    origin_nodes: dict[int, int],
    all_distances: dict[int, dict[int, float]],
) -> pd.DataFrame:
    """
    Compara distância em rede com distância euclidiana entre pares de origens.

    Retorna DataFrame com colunas:
    [origin, destination, euclidean_m, network_m, detour_ratio].
    """
    import math

    indices = list(origins.index)
    centroids = {idx: origins.loc[idx, "geometry"].centroid for idx in indices}
    rows = []
    for i, a in enumerate(indices):
        for b in indices[i + 1:]:
            ca = centroids[a]
            cb = centroids[b]
            euclid = math.sqrt((ca.x - cb.x) ** 2 + (ca.y - cb.y) ** 2)
            node_a = origin_nodes.get(a)
            node_b = origin_nodes.get(b)
            if node_a is not None and node_b is not None:
                net_dist = all_distances.get(node_a, {}).get(node_b, float("inf"))
            else:
                net_dist = float("inf")
            detour = (net_dist / euclid) if (euclid > 0 and net_dist < float("inf")) else None
            rows.append({
                "origin": origins.loc[a, origins_id_col],
                "destination": origins.loc[b, origins_id_col],
                "euclidean_m": round(euclid, 2),
                "network_m": round(net_dist, 2) if net_dist < float("inf") else None,
                "detour_ratio": round(detour, 4) if detour is not None else None,
            })
    return pd.DataFrame(rows)
