from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from sklearn.metrics.pairwise import rbf_kernel

from .weights import cross_knn_weights


@dataclass
class CovariateLagTransformer:
    k_neighbors: int = 8
    weighting: str = "uniform"
    distance_power: float = 1.0

    def fit(self, coordinates: np.ndarray, covariates: np.ndarray) -> "CovariateLagTransformer":
        coordinates = np.asarray(coordinates, dtype=float)
        covariates = np.asarray(covariates, dtype=float)
        if len(coordinates) != len(covariates):
            raise ValueError("coordinates and covariates must have the same number of rows")
        self._train_coordinates = coordinates
        self._train_covariates = covariates
        return self

    def transform_train(self) -> np.ndarray:
        indices, weights = cross_knn_weights(
            self._train_coordinates,
            self._train_coordinates,
            k=min(self.k_neighbors + 1, len(self._train_coordinates)),
            weighting=self.weighting,
            distance_power=self.distance_power,
        )
        out = np.empty_like(self._train_covariates, dtype=float)
        for i in range(len(indices)):
            mask = indices[i] != i
            idx = indices[i][mask][: self.k_neighbors]
            w = weights[i][mask][: self.k_neighbors]
            if len(idx) == 0:
                raise ValueError("not enough training observations for lag features")
            w = w / w.sum()
            out[i] = np.sum(self._train_covariates[idx] * w[:, None], axis=0)
        return out

    def transform_test(self, coordinates: np.ndarray) -> np.ndarray:
        indices, weights = cross_knn_weights(
            self._train_coordinates,
            np.asarray(coordinates, dtype=float),
            k=self.k_neighbors,
            weighting=self.weighting,
            distance_power=self.distance_power,
        )
        return np.einsum("ij,ijk->ik", weights, self._train_covariates[indices])


@dataclass
class SpatialEigenvectorTransformer:
    n_components: int = 32
    gamma: float = 0.5
    min_eigenvalue: float = 1e-8

    def fit(self, coordinates: np.ndarray) -> "SpatialEigenvectorTransformer":
        coords = np.asarray(coordinates, dtype=float)
        self._x_min = coords.min(axis=0)
        span = coords.max(axis=0) - self._x_min
        self._span = np.where(span == 0, 1.0, span)
        scaled = (coords - self._x_min) / self._span
        self._train_scaled = scaled
        kernel = rbf_kernel(scaled, scaled, gamma=self.gamma)
        self._train_col_mean = kernel.mean(axis=0)
        self._train_grand_mean = float(kernel.mean())
        centered = (
            kernel
            - kernel.mean(axis=0, keepdims=True)
            - kernel.mean(axis=1, keepdims=True)
            + self._train_grand_mean
        )
        eigenvalues, eigenvectors = np.linalg.eigh(centered)
        order = np.argsort(eigenvalues)[::-1]
        eigenvalues = eigenvalues[order]
        eigenvectors = eigenvectors[:, order]
        keep = eigenvalues > self.min_eigenvalue
        eigenvalues = eigenvalues[keep][: self.n_components]
        eigenvectors = eigenvectors[:, keep][:, : self.n_components]
        if len(eigenvalues) == 0:
            raise ValueError("no positive spatial eigenvalues were found")
        self._eigenvalues = eigenvalues
        self._eigenvectors = eigenvectors
        return self

    def transform(self, coordinates: np.ndarray) -> np.ndarray:
        coords = np.asarray(coordinates, dtype=float)
        scaled = (coords - self._x_min) / self._span
        kernel = rbf_kernel(scaled, self._train_scaled, gamma=self.gamma)
        row_mean = kernel.mean(axis=1, keepdims=True)
        centered = kernel - self._train_col_mean[None, :] - row_mean + self._train_grand_mean
        return centered @ self._eigenvectors / np.sqrt(self._eigenvalues[None, :])
