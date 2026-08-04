# Econometria Espacial — A4

Aplicação didática de econometria espacial de corte transversal.

## Modelos suportados

| Sigla | Nome | Parâmetro extra |
|-------|------|-----------------|
| OLS   | Ordinary Least Squares (referência) | — |
| SAR   | Spatial Autoregressive (lag em Y) | ρ ∈ (-1,1) |
| SEM   | Spatial Error Model | λ ∈ (-1,1) |
| SLX   | Spatial Lag of X | coeficientes θ de WX |
| SDM   | Spatial Durbin Model (SAR + WX) | ρ e θ |

> **Atenção**: os parâmetros ρ (SAR/SDM) e λ (SEM) **não são coeficientes OLS**;
> são estimados por máxima verossimilhança (ML) via concentração da verossimilhança.

## Decomposição de impactos

Para SAR e SDM, os efeitos de uma covariada são decompostos em:

- **Direto** — efeito médio sobre a própria unidade (diagonal de S(W)).
- **Indireto** — efeito médio sobre vizinhos (feedback espacial).
- **Total** — direto + indireto = média das linhas de S(W).

Fórmula:

```
S(W) = (I - ρW)⁻¹ β_k          (SAR)
S(W) = (I - ρW)⁻¹ (β_k I + θ_k W)  (SDM)
```

## Estrutura

```
econometria_espacial/
├── config/          # Configurações YAML
├── data/demo/       # Dados sintéticos gerados por SAR com parâmetros conhecidos
├── scripts/         # Script de geração de dados demo
├── src/
│   └── econometria_espacial/
│       ├── config.py       # AnalysisConfig, SpatialModelSpec
│       ├── weights.py      # WeightMatrix, load_weights
│       ├── models.py       # fit_spatial_model (OLS, SAR, SEM, SLX, SDM)
│       ├── impacts.py      # compute_impacts, impacts_table
│       ├── diagnostics.py  # moran_i, fit_comparison, residual_diagnostics
│       ├── reporting.py    # write_report, write_manifest
│       ├── pipeline.py     # run_pipeline
│       └── run.py          # CLI
└── tests/
```

## Uso

```bash
# Instalar dependências
pip install -e ".[dev]"

# Gerar dados demo (grade 5×5, SAR ρ=0.4)
python scripts/gerar_dados_demo.py

# Executar pipeline demo
python -m econometria_espacial.run --config config/demo.yml

# Testes
make test
```

## Distinção conceitual

- **Associação**: correlação observada sem controle de confundidores.
- **Mecanismo**: canal pelo qual a variável afeta o desfecho (direto vs. indireto).
- **Causalidade**: requer identificação exógena (IV, RDD, experimento). Os modelos
  aqui estimados descrevem *mecanismos plausíveis*, não relações causais.

## Referências

- Anselin, L. (1988). *Spatial Econometrics*. Kluwer.
- LeSage, J., Pace, R.K. (2009). *Introduction to Spatial Econometrics*. CRC Press.
