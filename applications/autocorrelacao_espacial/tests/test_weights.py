import numpy as np

from autocorrelacao_espacial.config import WeightSpec
from autocorrelacao_espacial.weights import build_weights


def test_rook_detects_island_and_components(grid_gdf):
    weights = build_weights(grid_gdf.sort_values("id").reset_index(drop=True), "id", WeightSpec(name="rook", type="rook"))
    assert weights.islands == ("island",)
    assert len(weights.components()) == 2
    assert weights.cardinalities.max() == 2


def test_queen_has_diagonal_neighbors(grid_gdf):
    ordered = grid_gdf.sort_values("id").reset_index(drop=True)
    rook = build_weights(ordered, "id", WeightSpec(name="rook", type="rook", transform="binary"))
    queen = build_weights(ordered, "id", WeightSpec(name="queen", type="queen", transform="binary"))
    assert queen.cardinalities[:4].sum() > rook.cardinalities[:4].sum()


def test_knn_union_removes_islands(grid_gdf):
    ordered = grid_gdf.sort_values("id").reset_index(drop=True)
    weights = build_weights(ordered, "id", WeightSpec(name="knn", type="knn", k=1, symmetrization="union"))
    assert not weights.islands
    assert len(weights.components()) == 1


def test_row_standardization_sums_to_one(grid_gdf):
    ordered = grid_gdf.sort_values("id").reset_index(drop=True)
    weights = build_weights(ordered, "id", WeightSpec(name="queen", type="queen", transform="row_standardized"))
    matrix = weights.dense()
    row_sums = matrix.sum(axis=1)
    assert np.allclose(row_sums[:4], 1.0)
    assert row_sums[4] == 0.0


def test_edge_list_preserves_ids(grid_gdf):
    ordered = grid_gdf.sort_values("id").reset_index(drop=True)
    weights = build_weights(ordered, "id", WeightSpec(name="rook", type="rook", transform="binary"))
    edges = weights.edge_list()
    assert {"origin_id", "destination_id", "weight"}.issubset(edges.columns)
    assert "island" not in set(edges["origin_id"])
