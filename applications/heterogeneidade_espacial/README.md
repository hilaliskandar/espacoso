# Heterogeneidade Espacial — GWR e MGWR

Aplicação didática para análise de relações espacialmente variáveis usando **GWR** (Geographically Weighted Regression) e **MGWR** (Multiscale GWR), com comparação a um modelo OLS global.

## Estrutura

```
heterogeneidade_espacial/
├── config/          # Configuração YAML
├── data/            # Dados de entrada (gerado por scripts/)
├── outputs/         # Produtos da análise
├── scripts/         # Scripts auxiliares (criação de dados demo)
├── src/
│   └── heterogeneidade_espacial/
│       ├── config.py          # Leitura e validação do YAML
│       ├── data.py            # Leitura de GeoPackage, extração de coordenadas
│       ├── global_model.py    # OLS global (statsmodels)
│       ├── gwr_model.py       # GWR e MGWR (mgwr)
│       ├── diagnostics.py     # Comparação, variabilidade, bootstrap
│       ├── cartography.py     # Mapas coropléticos e gráficos
│       ├── reporting.py       # Relatório Markdown e manifesto JSON
│       ├── pipeline.py        # Orquestração completa
│       └── run.py             # CLI
└── tests/
```

## Uso

```bash
# Instalar
make install

# Criar dados demo e executar
make run

# Só testes
make test
```

### CLI direta

```bash
heterogeneidade-espacial config/demo.yml
```

## Configuração

```yaml
data:
  path: data/demo/demo_gwr.gpkg
  layer: dados
  id_column: id

model:
  target: y
  predictors: [x1, x2]
  add_constant: true
  robust_covariance: HC3

bandwidth:
  criterion: AICc
  kernel: bisquare           # gaussian | bisquare | exponential
  fixed_or_adaptive: adaptive
  search_method: golden_section

run_mgwr: true

mgwr_bandwidth:
  criterion: AICc
  kernel: bisquare
  fixed_or_adaptive: adaptive
  search_method: golden_section

permutations: 99
seed: 42
alpha: 0.05
n_bootstrap: 0        # 0 = desabilita bootstrap
bootstrap_fraction: 0.8

output:
  dir: outputs/demo
```

## Produtos

| Arquivo | Conteúdo |
|---|---|
| `coeficientes_globais.csv` | Coeficientes OLS global |
| `resumo_modelos.csv` | R², AIC, BIC, RMSE por modelo |
| `vif_global.csv` | VIF (colinearidade global) |
| `coeficientes_gwr.csv` | Coeficientes locais GWR por observação |
| `variabilidade_gwr.csv` | Estatísticas descritivas dos coeficientes locais |
| `colinearidade_local_gwr.csv` | Diagnóstico de colinearidade local |
| `comparacao_modelos.csv` | Tabela comparativa OLS vs GWR vs MGWR |
| `heterogeneidade_espacial.gpkg` | GeoPackage com todos os resultados |
| `relatorio.md` | Relatório com notas metodológicas |
| `manifesto.json` | Proveniência e reprodutibilidade |
| `mapa_residuos_*.png` | Mapas de resíduos |
| `mapa_coef_gwr_*.png` | Superfícies de coeficientes locais |
| `mapa_se_gwr_*.png` | Superfícies de incerteza (erro padrão) |
| `comparacao_aic.png` | Comparação AIC por modelo |
| `comparacao_r2.png` | Comparação R² por modelo |

## Notas Metodológicas

- A **banda** (bandwidth) é selecionada via critério **AICc** por padrão. Bandas maiores → maior suavização → coeficientes mais próximos do modelo global.
- **MGWR** permite bandas distintas por preditor, capturando diferentes escalas de variação espacial.
- Coeficientes locais devem ser interpretados com **cautela**: múltiplas estimativas aumentam o risco de falsos positivos (*sobreinterpretação*).
- **Compare sempre** com o modelo global (OLS) antes de concluir sobre heterogeneidade.
- Use os **intervalos de confiança locais** para avaliar a incerteza de cada coeficiente.
- A **estabilidade por reamostragem** (bootstrap) pode ser ativada com `n_bootstrap > 0`.
