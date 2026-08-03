import numpy as np

from src.features import CovariateLagTransformer, SpatialEigenvectorTransformer


def test_lag_transformer_uses_training_reference_only_uniform():
    train_coords = np.array([[0, 0], [1, 0], [0, 1], [1, 1]], dtype=float)
    train_x = np.array([[1], [2], [3], [4]], dtype=float)
    test_coords = np.array([[10, 10]], dtype=float)
    tr = CovariateLagTransformer(k_neighbors=2, weighting="uniform").fit(
        train_coords, train_x
    )
    train_lag = tr.transform_train()
    test_lag = tr.transform_test(test_coords)
    assert train_lag.shape == train_x.shape
    assert test_lag.shape == (1, 1)
    assert 1 <= test_lag[0, 0] <= 4


def test_lag_transformer_inverse_distance_is_finite():
    train_coords = np.array([[0, 0], [1, 0], [0, 1], [1, 1]], dtype=float)
    train_x = np.array([[1], [2], [3], [4]], dtype=float)
    tr = CovariateLagTransformer(k_neighbors=3, weighting="inverse_distance").fit(
        train_coords, train_x
    )
    assert np.isfinite(tr.transform_train()).all()
    assert np.isfinite(tr.transform_test(np.array([[0.2, 0.2]]))).all()


def test_spatial_eigenvectors_project_test_rows():
    rng = np.random.default_rng(2)
    train = rng.normal(size=(20, 2))
    test = rng.normal(size=(5, 2))
    basis = SpatialEigenvectorTransformer(n_components=8, gamma=0.5).fit(train)
    assert basis.transform(train).shape == (20, 8)
    assert basis.transform(test).shape == (5, 8)
    assert np.isfinite(basis.transform(test)).all()
