"""Validação topológica da rede viária."""
from __future__ import annotations

from dataclasses import dataclass

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.geometry import MultiLineString, Point


@dataclass
class TopologyReport:
    n_edges: int
    n_nodes: int
    n_components: int
    n_isolated_nodes: int
    isolated_node_ids: list[int]
    has_duplicate_edges: bool
    total_length_m: float

    def to_dict(self) -> dict:
        return {
            "n_edges": self.n_edges,
            "n_nodes": self.n_nodes,
            "n_components": self.n_components,
            "n_isolated_nodes": self.n_isolated_nodes,
            "isolated_node_ids": self.isolated_node_ids,
            "has_duplicate_edges": self.has_duplicate_edges,
            "total_length_m": round(self.total_length_m, 2),
        }


def _endpoints(geom) -> tuple[tuple[float, float], tuple[float, float]]:
    """Retorna os pontos inicial e final de uma geometria de linha."""
    if geom.geom_type == "MultiLineString":
        coords = list(geom.geoms[0].coords)
        end_coords = list(geom.geoms[-1].coords)
        return (coords[0][0], coords[0][1]), (end_coords[-1][0], end_coords[-1][1])
    coords = list(geom.coords)
    return (coords[0][0], coords[0][1]), (coords[-1][0], coords[-1][1])


def build_node_index(
    network: gpd.GeoDataFrame, tolerance: float = 1e-3
) -> dict[tuple[float, float], int]:
    """Constrói índice de nós a partir dos extremos das arestas."""
    raw_points: list[tuple[float, float]] = []
    for geom in network.geometry:
        start, end = _endpoints(geom)
        raw_points.extend([start, end])

    # Snap points within tolerance to a common representative
    node_map: dict[tuple[float, float], int] = {}
    node_id = 0
    for pt in raw_points:
        matched = False
        for existing in node_map:
            if abs(pt[0] - existing[0]) < tolerance and abs(pt[1] - existing[1]) < tolerance:
                node_map[pt] = node_map[existing]
                matched = True
                break
        if not matched:
            node_map[pt] = node_id
            node_id += 1
    return node_map


def build_adjacency(
    network: gpd.GeoDataFrame,
    node_map: dict[tuple[float, float], int],
    directed: bool = False,
) -> dict[int, list[tuple[int, float]]]:
    """
    Constrói lista de adjacência ponderada pelo comprimento.

    Retorna: {nó_origem: [(nó_destino, peso), ...]}
    """
    adj: dict[int, list[tuple[int, float]]] = {}
    n_nodes = max(node_map.values()) + 1 if node_map else 0
    for i in range(n_nodes):
        adj[i] = []

    for _, row in network.iterrows():
        start, end = _endpoints(row.geometry)
        # Find closest node for start/end
        u = _snap_node(start, node_map)
        v = _snap_node(end, node_map)
        weight = float(row["length_m"])
        if u is None or v is None:
            continue
        adj[u].append((v, weight))
        if not directed:
            adj[v].append((u, weight))
    return adj


def _snap_node(
    pt: tuple[float, float],
    node_map: dict[tuple[float, float], int],
    tolerance: float = 1e-3,
) -> int | None:
    """Encontra o nó mais próximo dentro da tolerância."""
    for existing, node_id in node_map.items():
        if abs(pt[0] - existing[0]) < tolerance and abs(pt[1] - existing[1]) < tolerance:
            return node_id
    return None


def _connected_components(adj: dict[int, list[tuple[int, float]]]) -> list[set[int]]:
    """Encontra componentes conexas via BFS."""
    visited: set[int] = set()
    components: list[set[int]] = []
    for start in adj:
        if start in visited:
            continue
        component: set[int] = set()
        queue = [start]
        while queue:
            node = queue.pop()
            if node in visited:
                continue
            visited.add(node)
            component.add(node)
            for neighbor, _ in adj[node]:
                if neighbor not in visited:
                    queue.append(neighbor)
        components.append(component)
    return components


def validate_topology(
    network: gpd.GeoDataFrame,
    directed: bool = False,
) -> TopologyReport:
    """Valida topologia da rede e retorna relatório."""
    node_map = build_node_index(network)
    adj = build_adjacency(network, node_map, directed=directed)
    components = _connected_components(adj)

    isolated = [next(iter(c)) for c in components if len(c) == 1]

    # Check duplicate edges
    edge_set: set[tuple[int, int]] = set()
    has_duplicates = False
    for _, row in network.iterrows():
        start, end = _endpoints(row.geometry)
        u = _snap_node(start, node_map)
        v = _snap_node(end, node_map)
        if u is None or v is None:
            continue
        edge_key = (min(u, v), max(u, v))
        if edge_key in edge_set:
            has_duplicates = True
            break
        edge_set.add(edge_key)

    return TopologyReport(
        n_edges=len(network),
        n_nodes=len(adj),
        n_components=len(components),
        n_isolated_nodes=len(isolated),
        isolated_node_ids=isolated,
        has_duplicate_edges=has_duplicates,
        total_length_m=float(network["length_m"].sum()),
    )
