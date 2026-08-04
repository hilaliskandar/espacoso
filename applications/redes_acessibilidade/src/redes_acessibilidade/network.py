"""Algoritmos de rede: caminhos mínimos, centralidade."""
from __future__ import annotations

import heapq
from dataclasses import dataclass

import geopandas as gpd
import numpy as np
import pandas as pd

from .topology import build_adjacency, build_node_index, _snap_node


@dataclass
class ShortestPathResult:
    """Resultado dos caminhos mínimos a partir de uma origem."""
    origin_node: int
    distances: dict[int, float]  # node_id -> cost


def dijkstra(
    adj: dict[int, list[tuple[int, float]]],
    source: int,
    max_cost: float = float("inf"),
) -> dict[int, float]:
    """
    Algoritmo de Dijkstra a partir de um nó fonte.

    Retorna dicionário {nó: custo_mínimo}.
    """
    dist: dict[int, float] = {source: 0.0}
    heap: list[tuple[float, int]] = [(0.0, source)]
    while heap:
        cost, u = heapq.heappop(heap)
        if cost > dist.get(u, float("inf")):
            continue
        for v, w in adj.get(u, []):
            new_cost = cost + w
            if new_cost <= max_cost and new_cost < dist.get(v, float("inf")):
                dist[v] = new_cost
                heapq.heappush(heap, (new_cost, v))
    return dist


def compute_all_pairs_shortest_paths(
    adj: dict[int, list[tuple[int, float]]],
    nodes: list[int],
    max_cost: float = float("inf"),
) -> dict[int, dict[int, float]]:
    """Caminhos mínimos entre todos os pares de nós fornecidos."""
    return {node: dijkstra(adj, node, max_cost) for node in nodes}


def snap_origins_to_network(
    origins: gpd.GeoDataFrame,
    network: gpd.GeoDataFrame,
    node_map: dict[tuple[float, float], int],
) -> dict[int, int]:
    """
    Para cada origem (índice do GeoDataFrame), encontra o nó da rede mais próximo.

    Retorna {índice_origem: node_id}.
    """
    nodes_xy = {nid: pt for pt, nid in node_map.items()}
    # Build arrays for vectorized nearest-node lookup
    node_ids = list(nodes_xy.keys())
    node_coords = np.array([[nodes_xy[n][0], nodes_xy[n][1]] for n in node_ids])

    result: dict[int, int] = {}
    for idx, row in origins.iterrows():
        cx = row.geometry.centroid.x
        cy = row.geometry.centroid.y
        dists = np.sqrt((node_coords[:, 0] - cx) ** 2 + (node_coords[:, 1] - cy) ** 2)
        nearest_pos = int(np.argmin(dists))
        result[idx] = node_ids[nearest_pos]
    return result


def betweenness_centrality(
    adj: dict[int, list[tuple[int, float]]],
    normalized: bool = True,
) -> dict[int, float]:
    """
    Centralidade de intermediação (Brandes, 2001) — versão ponderada simplificada.

    Para redes de tamanho didático (< 500 nós).
    """
    nodes = list(adj.keys())
    n = len(nodes)
    cb: dict[int, float] = {v: 0.0 for v in nodes}

    for s in nodes:
        # BFS/Dijkstra para caminhos mínimos
        dist = {v: float("inf") for v in nodes}
        sigma: dict[int, int] = {v: 0 for v in nodes}
        pred: dict[int, list[int]] = {v: [] for v in nodes}
        dist[s] = 0.0
        sigma[s] = 1
        heap: list[tuple[float, int]] = [(0.0, s)]
        visited_order: list[int] = []

        while heap:
            d, v = heapq.heappop(heap)
            if d > dist[v]:
                continue
            visited_order.append(v)
            for w, weight in adj.get(v, []):
                new_d = dist[v] + weight
                if new_d < dist[w]:
                    dist[w] = new_d
                    sigma[w] = sigma[v]
                    pred[w] = [v]
                    heapq.heappush(heap, (new_d, w))
                elif new_d == dist[w]:
                    sigma[w] += sigma[v]
                    pred[w].append(v)

        delta: dict[int, float] = {v: 0.0 for v in nodes}
        for w in reversed(visited_order):
            for v in pred[w]:
                if sigma[w] > 0:
                    delta[v] += (sigma[v] / sigma[w]) * (1.0 + delta[w])
            if w != s:
                cb[w] += delta[w]

    if normalized and n > 2:
        scale = 1.0 / ((n - 1) * (n - 2))
        cb = {v: cb[v] * scale for v in cb}
    return cb


def closeness_centrality(
    adj: dict[int, list[tuple[int, float]]],
) -> dict[int, float]:
    """Centralidade de proximidade (normalizada pelo componente)."""
    nodes = list(adj.keys())
    n = len(nodes)
    result: dict[int, float] = {}
    for s in nodes:
        dist = dijkstra(adj, s)
        reachable = [d for v, d in dist.items() if v != s and d < float("inf")]
        if not reachable:
            result[s] = 0.0
        else:
            avg = sum(reachable) / len(reachable)
            # Wasserman & Faust normalisation
            result[s] = (len(reachable) / (n - 1)) * (len(reachable) / sum(reachable)) if sum(reachable) > 0 else 0.0
    return result


def degree_centrality(
    adj: dict[int, list[tuple[int, float]]],
) -> dict[int, float]:
    """Centralidade de grau (normalizada)."""
    nodes = list(adj.keys())
    n = len(nodes)
    if n <= 1:
        return {v: 0.0 for v in nodes}
    return {v: len(adj[v]) / (n - 1) for v in nodes}
