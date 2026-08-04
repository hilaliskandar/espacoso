#!/usr/bin/env python
"""Gera dados simulados de painel espaço-temporal para demonstração.

O painel simulado consiste em N unidades (regiões) observadas ao longo de T períodos
com uma variável dependente com dependência espacial e temporal.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


def generate_panel(
    n_units: int = 20,
    n_periods: int = 5,
    rho: float = 0.3,
    seed: int = 20260701,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Gera painel simulado com dependência espacial.

    Returns
    -------
    (panel_df, weights_df)
    """
    rng = np.random.default_rng(seed)

    # Posições fixas das unidades em grade quadrada
    side = int(np.ceil(np.sqrt(n_units)))
    coords = [(i, j) for i in range(side) for j in range(side)][:n_units]
    unit_ids = [f"U{i:03d}" for i in range(n_units)]

    # Matriz de contiguidade rainha simples (vizinhos em grade)
    def are_neighbors(a: tuple[int, int], b: tuple[int, int]) -> bool:
        return abs(a[0] - b[0]) <= 1 and abs(a[1] - b[1]) <= 1 and a != b

    edges = []
    for i, (uid, ci) in enumerate(zip(unit_ids, coords)):
        for j, (ujd, cj) in enumerate(zip(unit_ids, coords)):
            if are_neighbors(ci, cj):
                edges.append({"origin_id": uid, "destination_id": ujd, "weight": 1.0})

    weights_df = pd.DataFrame(edges)
    # Row-standardize
    row_sums = weights_df.groupby("origin_id")["weight"].transform("sum")
    weights_df["weight"] = weights_df["weight"] / row_sums

    # Construir W densa
    W = np.zeros((n_units, n_units))
    idx = {u: i for i, u in enumerate(unit_ids)}
    for _, row in weights_df.iterrows():
        W[idx[row["origin_id"]], idx[row["destination_id"]]] = row["weight"]

    # Efeitos fixos de unidade e de tempo
    unit_fe = rng.normal(0, 1, n_units)
    time_fe = rng.normal(0, 0.5, n_periods)

    periods = list(range(2020, 2020 + n_periods))

    # Preditores
    x1 = rng.normal(2, 1, (n_units, n_periods))
    x2 = rng.normal(0, 1, (n_units, n_periods))

    rows = []
    for t_idx, period in enumerate(periods):
        # Resolução do modelo de lag espacial: (I - ρW)y = Xβ + FE + ε
        epsilon = rng.normal(0, 0.5, n_units)
        lin_pred = (
            0.8 * x1[:, t_idx]
            + (-0.4) * x2[:, t_idx]
            + unit_fe
            + time_fe[t_idx]
            + epsilon
        )
        IrW = np.eye(n_units) - rho * W
        try:
            y = np.linalg.solve(IrW, lin_pred)
        except np.linalg.LinAlgError:
            y = lin_pred  # fallback

        for i, uid in enumerate(unit_ids):
            rows.append({
                "unit_id": uid,
                "time_id": period,
                "x1": round(float(x1[i, t_idx]), 4),
                "x2": round(float(x2[i, t_idx]), 4),
                "y": round(float(y[i]), 4),
            })

    panel_df = pd.DataFrame(rows)
    return panel_df, weights_df


def main() -> None:
    parser = argparse.ArgumentParser(description="Gera dados de demonstração para paineis_espaciais.")
    parser.add_argument("--output-dir", default="data/demo", help="Diretório de saída.")
    parser.add_argument("--n-units", type=int, default=20)
    parser.add_argument("--n-periods", type=int, default=5)
    parser.add_argument("--seed", type=int, default=20260701)
    args = parser.parse_args()

    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)

    panel_df, weights_df = generate_panel(
        n_units=args.n_units,
        n_periods=args.n_periods,
        seed=args.seed,
    )

    panel_path = out / "painel_demo.csv"
    weights_path = out / "pesos_queen.csv"
    panel_df.to_csv(panel_path, index=False)
    weights_df.to_csv(weights_path, index=False)

    # Introduzir painel desbalanceado (remover 3 obs aleatórias)
    rng = np.random.default_rng(args.seed + 1)
    drop_idx = rng.choice(len(panel_df), size=3, replace=False)
    panel_unbal = panel_df.drop(index=drop_idx).reset_index(drop=True)
    panel_unbal.to_csv(out / "painel_demo_desbalanceado.csv", index=False)

    print(f"Dados gerados em: {out}")
    print(f"  {panel_path.name}: {len(panel_df)} observações")
    print(f"  {weights_path.name}: {len(weights_df)} arestas")
    print(f"  painel_demo_desbalanceado.csv: {len(panel_unbal)} observações")


if __name__ == "__main__":
    main()
