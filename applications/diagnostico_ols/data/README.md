# Dados da A3

Dados brutos e produtos regeneráveis não são versionados.

A demonstração é gerada por:

```bash
python scripts/create_demo_data.py --output-dir data/demo
```

O script produz:

- `demo_ols.gpkg`: grade sintética com `y`, `x1`, `x2` e `z_spatial`;
- `pesos_rook.csv`;
- `pesos_queen.csv`.

A fixture é exclusivamente didática e não sustenta conclusões territoriais reais.
