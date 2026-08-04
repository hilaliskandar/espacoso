"""Testes das funções de impedância e acessibilidade."""
from __future__ import annotations

import math

import pandas as pd
import pytest

from redes_acessibilidade.accessibility import (
    impedance_linear,
    impedance_negative_exponential,
    impedance_binary,
    impedance_power,
    apply_impedance,
    compute_accessibility,
    compare_network_vs_euclidean,
)
from redes_acessibilidade.config import ImpedanceSpec


# ---------------------------------------------------------------------------
# Funções de impedância
# ---------------------------------------------------------------------------

def test_impedance_linear_at_zero():
    assert impedance_linear(0, 5000) == pytest.approx(1.0)


def test_impedance_linear_at_cutoff():
    assert impedance_linear(5000, 5000) == pytest.approx(0.0)


def test_impedance_linear_beyond_cutoff():
    assert impedance_linear(6000, 5000) == pytest.approx(0.0)


def test_impedance_linear_midpoint():
    assert impedance_linear(2500, 5000) == pytest.approx(0.5)


def test_impedance_negative_exponential_at_zero():
    assert impedance_negative_exponential(0, 0.001) == pytest.approx(1.0)


def test_impedance_negative_exponential_decays():
    v1 = impedance_negative_exponential(1000, 0.001)
    v2 = impedance_negative_exponential(2000, 0.001)
    assert v1 > v2 > 0


def test_impedance_negative_exponential_formula():
    beta = 0.001
    cost = 3000
    assert impedance_negative_exponential(cost, beta) == pytest.approx(math.exp(-beta * cost))


def test_impedance_binary_within():
    assert impedance_binary(999, 1000) == pytest.approx(1.0)


def test_impedance_binary_at_cutoff():
    assert impedance_binary(1000, 1000) == pytest.approx(1.0)


def test_impedance_binary_beyond():
    assert impedance_binary(1001, 1000) == pytest.approx(0.0)


def test_impedance_power_at_zero():
    assert impedance_power(0, 2.0) == pytest.approx(1.0)


def test_impedance_power_decreases():
    assert impedance_power(1000, 2.0) < impedance_power(500, 2.0)


def test_apply_impedance_linear():
    spec = ImpedanceSpec(name="lin", function="linear", cutoff=5000.0)
    assert apply_impedance(0.0, spec) == pytest.approx(1.0)
    assert apply_impedance(5000.0, spec) == pytest.approx(0.0)


def test_apply_impedance_exp():
    spec = ImpedanceSpec(name="exp", function="negative_exponential", beta=0.001)
    assert apply_impedance(0.0, spec) == pytest.approx(1.0)


def test_invalid_impedance_function():
    spec = ImpedanceSpec(name="x", function="unknown")
    with pytest.raises(ValueError, match="desconhecida"):
        apply_impedance(100, spec)


# ---------------------------------------------------------------------------
# Acessibilidade
# ---------------------------------------------------------------------------

def test_compute_accessibility_basic():
    """Origem próxima deve ter maior acessibilidade que origem distante."""
    # Two origins: A at node 0, B at node 2
    origin_nodes = {0: 0, 1: 2}
    # One destination at node 1 with 100 opportunities
    destinations = pd.DataFrame([{"_node": 1, "opp": 100.0}])
    # distances: 0->1=500, 2->1=2000
    all_distances = {
        0: {0: 0.0, 1: 500.0, 2: 2500.0},
        2: {0: 2500.0, 1: 2000.0, 2: 0.0},
    }
    spec = ImpedanceSpec(name="lin", function="linear", cutoff=5000.0)
    result = compute_accessibility(
        origin_nodes=origin_nodes,
        destinations=destinations,
        destination_node_col="_node",
        opportunities_col="opp",
        all_distances=all_distances,
        spec=spec,
    )
    assert result[0] > result[1]


def test_compare_network_vs_euclidean(simple_network, simple_origins):
    from redes_acessibilidade.topology import build_node_index, build_adjacency
    from redes_acessibilidade.network import snap_origins_to_network, dijkstra

    node_map = build_node_index(simple_network)
    adj = build_adjacency(simple_network, node_map)
    origin_nodes = snap_origins_to_network(simple_origins, simple_network, node_map)

    all_dist = {n: dijkstra(adj, n) for n in set(origin_nodes.values())}

    df = compare_network_vs_euclidean(simple_origins, "id", origin_nodes, all_dist)
    assert "euclidean_m" in df.columns
    assert "network_m" in df.columns
    assert "detour_ratio" in df.columns
    # network distance >= euclidean distance (triangle inequality)
    valid = df.dropna(subset=["euclidean_m", "network_m"])
    for _, row in valid.iterrows():
        if row["network_m"] is not None:
            assert row["network_m"] >= row["euclidean_m"] - 1e-3
