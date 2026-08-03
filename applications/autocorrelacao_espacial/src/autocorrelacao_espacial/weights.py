from __future__ import annotations

from dataclasses import dataclass

import geopandas as gpd
import numpy as np
import pandas as pd

from .config import WeightSpec
from .errors import WeightsError


@dataclass(frozen=True)
class WeightMatrix:
    name: str
    ids: tuple[str, ...]
    neighbors: tuple[tuple[int, ...], ...]
    weights: tuple[tuple[float, ...], ...]
    transform: str
    kind: str
    metadata: dict

    @property
    def n(self) -> int:
        return len(self.ids)

    @property
    def s0(self) -> float:
        return float(sum(sum(row) for row in self.weights))

    @property
    def cardinalities(self) -> np.ndarray:
        return np.asarray([len(row) for row in self.neighbors], dtype=int)

    @property
    def islands(self) -> tuple[str, ...]:
        return tuple(self.ids[i] for i, row in enumerate(self.neighbors) if not row)

    def dense(self) -> np.ndarray:
        matrix = np.zeros((self.n, self.n), dtype=float)
        for i, (nbrs, vals) in enumerate(zip(self.neighbors, self.weights, strict=True)):
            if nbrs:
                matrix[i, np.asarray(nbrs, dtype=int)] = np.asarray(vals, dtype=float)
        return matrix

    def lag(self, values: np.ndarray) -> np.ndarray:
        values = np.asarray(values, dtype=float)
        if values.shape != (self.n,):
            raise WeightsError("O vetor não está alinhado à matriz de pesos.")
        return self.dense() @ values

    def components(self) -> list[list[int]]:
        adjacency = [set(row) for row in self.neighbors]
        for i, row in enumerate(self.neighbors):
            for j in row:
                adjacency[j].add(i)
        unseen = set(range(self.n))
        components: list[list[int]] = []
        while unseen:
            start = min(unseen)
            stack = [start]
            unseen.remove(start)
            component: list[int] = []
            while stack:
                node = stack.pop()
                component.append(node)
                for nbr in sorted(adjacency[node]):
                    if nbr in unseen:
                        unseen.remove(nbr)
                        stack.append(nbr)
            components.append(sorted(component))
        return components

    def diagnostics(self) -> dict:
        cards = self.cardinalities
        components = self.components()
        return {
            "name": self.name,
            "type": self.kind,
            "transform": self.transform,
            "n": self.n,
            "s0": self.s0,
            "islands": len(self.islands),
            "island_ids": list(self.islands),
            "components": len(components),
            "largest_component": max(len(c) for c in components),
            "mean_neighbors": float(cards.mean()),
            "min_neighbors": int(cards.min()),
            "max_neighbors": int(cards.max()),
            **self.metadata,
        }

    def edge_list(self) -> pd.DataFrame:
        rows: list[dict] = []
        for i, (nbrs, vals) in enumerate(zip(self.neighbors, self.weights, strict=True)):
            for j, value in zip(nbrs, vals, strict=True):
                rows.append(
                    {
                        "origin_index": i,
                        "origin_id": self.ids[i],
                        "destination_index": j,
                        "destination_id": self.ids[j],
                        "weight": float(value),
                    }
                )
        return pd.DataFrame(rows)


def _apply_transform(rows: list[dict[int, float]], transform: str) -> list[dict[int, float]]:
    if transform == "binary":
        return [{j: 1.0 for j in sorted(row)} for row in rows]
    if transform == "row_standardized":
        transformed: list[dict[int, float]] = []
        for row in rows:
            total = float(sum(row.values()))
            transformed.append({j: float(value / total) for j, value in sorted(row.items())} if total else {})
        return transformed
    raise WeightsError(f"Transformação desconhecida: {transform}")


def _symmetrize(rows: list[dict[int, float]], mode: str) -> list[dict[int, float]]:
    if mode == "none":
        return rows
    n = len(rows)
    result = [dict(row) for row in rows]
    if mode == "union":
        for i in range(n):
            for j, value in list(rows[i].items()):
                if i not in result[j]:
                    result[j][i] = value
        return result
    if mode == "mutual":
        for i in range(n):
            result[i] = {j: value for j, value in rows[i].items() if i in rows[j]}
        return result
    raise WeightsError(f"Simetrização desconhecida: {mode}")


def _contiguity_rows(gdf: gpd.GeoDataFrame, kind: str, tolerance: float) -> list[dict[int, float]]:
    n = len(gdf)
    rows = [dict() for _ in range(n)]
    geometries = list(gdf.geometry)
    for i in range(n):
        boundary_i = geometries[i].boundary
        for j in range(i + 1, n):
            boundary_j = geometries[j].boundary
            intersection = boundary_i.intersection(boundary_j)
            if intersection.is_empty:
                continue
            is_neighbor = kind == "queen" or float(intersection.length) > tolerance
            if is_neighbor:
                rows[i][j] = 1.0
                rows[j][i] = 1.0
    return rows


def _centroid_coordinates(gdf: gpd.GeoDataFrame) -> np.ndarray:
    centroids = gdf.geometry.centroid
    return np.column_stack([centroids.x.to_numpy(), centroids.y.to_numpy()]).astype(float)


def _distance_matrix(coords: np.ndarray) -> np.ndarray:
    diff = coords[:, None, :] - coords[None, :, :]
    return np.sqrt(np.sum(diff * diff, axis=2))


def _knn_rows(gdf: gpd.GeoDataFrame, k: int, symmetrization: str) -> list[dict[int, float]]:
    n = len(gdf)
    if k >= n:
        raise WeightsError(f"k={k} deve ser menor que n={n}.")
    distances = _distance_matrix(_centroid_coordinates(gdf))
    np.fill_diagonal(distances, np.inf)
    rows = [dict() for _ in range(n)]
    for i in range(n):
        order = np.lexsort((np.arange(n), distances[i]))
        for j in order[:k]:
            rows[i][int(j)] = 1.0
    return _symmetrize(rows, symmetrization)


def _distance_rows(
    gdf: gpd.GeoDataFrame,
    threshold: float,
    power: float,
    symmetrization: str,
) -> list[dict[int, float]]:
    n = len(gdf)
    distances = _distance_matrix(_centroid_coordinates(gdf))
    rows = [dict() for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            distance = float(distances[i, j])
            if distance <= threshold:
                value = 1.0 if power == 0 else 1.0 / (distance**power)
                rows[i][j] = value
    return _symmetrize(rows, symmetrization)


def build_weights(gdf: gpd.GeoDataFrame, id_column: str, spec: WeightSpec) -> WeightMatrix:
    ids = tuple(gdf[id_column].astype(str).tolist())
    if len(ids) < 3:
        raise WeightsError("São necessárias ao menos três unidades territoriais.")
    if spec.type in {"rook", "queen"}:
        rows = _contiguity_rows(gdf, spec.type, spec.boundary_tolerance)
    elif spec.type == "knn":
        assert spec.k is not None
        rows = _knn_rows(gdf, spec.k, spec.symmetrization)
    elif spec.type == "distance":
        assert spec.threshold is not None
        rows = _distance_rows(gdf, spec.threshold, spec.distance_power, spec.symmetrization)
    else:
        raise WeightsError(f"Tipo desconhecido: {spec.type}")
    rows = _apply_transform(rows, spec.transform)
    neighbors = tuple(tuple(sorted(row)) for row in rows)
    weights = tuple(tuple(float(row[j]) for j in sorted(row)) for row in rows)
    metadata = {
        "k": spec.k,
        "threshold": spec.threshold,
        "distance_power": spec.distance_power,
        "symmetrization": spec.symmetrization,
    }
    return WeightMatrix(
        name=spec.name,
        ids=ids,
        neighbors=neighbors,
        weights=weights,
        transform=spec.transform,
        kind=spec.type,
        metadata=metadata,
    )
