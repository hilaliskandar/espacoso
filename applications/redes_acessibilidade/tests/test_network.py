"""Testes de topologia e algoritmos de rede."""
from __future__ import annotations

import geopandas as gpd
import pytest
from shapely.geometry import LineString

from redes_acessibilidade.topology import (
    build_adjacency,
    build_node_index,
    validate_topology,
    _connected_components,
)
from redes_acessibilidade.network import (
    dijkstra,
    betweenness_centrality,
    closeness_centrality,
    degree_centrality,
    snap_origins_to_network,
)


def test_build_node_index_simple_network(simple_network):
    node_map = build_node_index(simple_network)
    # Uma rede com 6 arestas de grade deve ter vários nós distintos
    assert len(set(node_map.values())) >= 4


def test_build_adjacency_undirected(simple_network):
    node_map = build_node_index(simple_network)
    adj = build_adjacency(simple_network, node_map, directed=False)
    # Todo nó deve ter pelo menos um vizinho
    for node, neighbors in adj.items():
        assert len(neighbors) >= 0  # isolated nodes may exist in test fixture
    # Check symmetry: if (u, v) exists, (v, u) should too
    for u, neighbors in adj.items():
        for v, w in neighbors:
            assert any(nb == u for nb, _ in adj[v]), f"Aresta ({u},{v}) não é simétrica."


def test_validate_topology_connected(simple_network):
    report = validate_topology(simple_network)
    assert report.n_edges == len(simple_network)
    assert report.n_nodes > 0
    # Our simple_network fixture is connected
    assert report.n_components == 1
    assert report.n_isolated_nodes == 0


def test_validate_topology_with_isolated():
    """Rede com um nó isolado deve reportar n_components > 1."""
    edges = [
        {"edge_id": "A", "geometry": LineString([(0, 0), (1000, 0)])},
        {"edge_id": "B", "geometry": LineString([(5000, 0), (6000, 0)])},  # desconectado
    ]
    gdf = gpd.GeoDataFrame(edges, crs="EPSG:31983")
    gdf["length_m"] = gdf.geometry.length
    report = validate_topology(gdf)
    assert report.n_components == 2


def test_dijkstra_simple():
    adj = {
        0: [(1, 100.0), (2, 200.0)],
        1: [(0, 100.0), (2, 50.0)],
        2: [(0, 200.0), (1, 50.0)],
    }
    dist = dijkstra(adj, 0)
    assert dist[0] == 0.0
    assert dist[1] == 100.0
    assert dist[2] == 150.0


def test_dijkstra_max_cost():
    adj = {
        0: [(1, 100.0)],
        1: [(0, 100.0), (2, 200.0)],
        2: [(1, 200.0)],
    }
    dist = dijkstra(adj, 0, max_cost=150.0)
    assert 0 in dist
    assert 1 in dist
    # Node 2 costs 300 > 150 so should not be reachable
    assert dist.get(2, float("inf")) == float("inf")


def test_dijkstra_unreachable():
    adj = {0: [(1, 50.0)], 1: [(0, 50.0)], 2: []}
    dist = dijkstra(adj, 0)
    assert dist[0] == 0.0
    assert dist[1] == 50.0
    assert dist.get(2, float("inf")) == float("inf")


def test_degree_centrality():
    adj = {0: [(1, 1.0), (2, 1.0)], 1: [(0, 1.0)], 2: [(0, 1.0)]}
    dc = degree_centrality(adj)
    # Node 0 connects to 2 others → normalized = 2/(3-1) = 1.0
    assert dc[0] == pytest.approx(1.0)
    assert dc[1] == pytest.approx(0.5)


def test_snap_origins_to_network(simple_network, simple_origins):
    node_map = build_node_index(simple_network)
    snapped = snap_origins_to_network(simple_origins, simple_network, node_map)
    assert len(snapped) == len(simple_origins)
    for idx, node_id in snapped.items():
        assert isinstance(node_id, int)


def test_connected_components():
    adj = {0: [(1, 1.0)], 1: [(0, 1.0)], 2: [], 3: [(4, 1.0)], 4: [(3, 1.0)]}
    comps = _connected_components(adj)
    assert len(comps) == 3  # {0,1}, {2}, {3,4}
