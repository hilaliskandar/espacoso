import numpy as np

from src.spatial_cv import (
    ValidationDesign,
    apply_buffer,
    build_splits,
    make_spatial_grid_groups,
    spatial_splits,
)


def test_spatial_groups_and_splits_are_disjoint():
    rng = np.random.default_rng(1)
    coords = rng.uniform(size=(100, 2))
    groups = make_spatial_grid_groups(coords, n_cols=4, n_rows=4)
    for train_idx, test_idx in spatial_splits(groups, n_splits=4):
        assert set(train_idx).isdisjoint(set(test_idx))
        assert set(groups[train_idx]).isdisjoint(set(groups[test_idx]))


def test_buffer_removes_near_training_points():
    coords = np.array([[0, 0], [0.05, 0], [1, 1], [2, 2], [3, 3], [4, 4]], dtype=float)
    train = np.array([1, 2, 3, 4, 5])
    test = np.array([0])
    filtered = apply_buffer(train, test, coords, buffer_distance=0.1)
    assert 1 not in filtered
    assert 2 in filtered


def test_build_splits_supports_multiple_designs():
    rng = np.random.default_rng(5)
    coords = rng.uniform(size=(90, 2))
    random_design = ValidationDesign("random", "random", 3)
    spatial_design = ValidationDesign("spatial", "spatial", 3, n_rows=3, n_cols=3)
    assert len(list(build_splits(coords, random_design, 1))) == 3
    assert len(list(build_splits(coords, spatial_design, 1))) == 3
