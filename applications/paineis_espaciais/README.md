# Painéis Espaciais e Dinâmica Territorial

Aplicação longitudinal do curso Espaçoso (A7), organizando dados unidade–tempo
e comparando especificações não espaciais e espaciais.

## Funcionalidades

- Construção de painel com índice único e ordenado por (unidade, tempo)
- Diagnóstico de balanço e tratamento explícito de lacunas
- Efeitos fixos de unidade, de tempo ou bidirecional (within demeaning)
- Modelo de lag espacial estático via IV/2SLS
- Modelo de erro espacial via GM iterativo (Cochrane-Orcutt espacial)
- Modelo dinâmico com defasagem temporal e aviso sobre limites de identificação
- Comparação de resultados e diagnóstico tabelado
- Relatório Markdown, CLI, configuração YAML e manifesto de proveniência

## Instalação

```bash
cd applications/paineis_espaciais
make install
```

## Uso rápido

```bash
# Gerar dados de demonstração e executar pipeline
make run

# Apenas os testes
make test
```

## CLI

```bash
paineis-espaciais config/demo.yml
```

## Configuração (YAML)

```yaml
data:
  path: dados/painel.csv
  unit_col: unit_id
  time_col: time_id

gap_strategy: forward_fill  # none | forward_fill | backward_fill | interpolate
gap_limit: 1

models:
  - name: fe_baseline
    target: y
    predictors: [x1, x2]
    fixed_effects: unit       # unit | time | two_way
    model_type: fe            # fe | spatial_lag | spatial_error
    dynamic: false            # inclui y_lag1 como regressor

  - name: lag_espacial
    target: y
    predictors: [x1, x2]
    fixed_effects: unit
    model_type: spatial_lag

weights:
  - name: queen
    path: dados/pesos_queen.csv
    transformation: row_standardized
    time_varying: false

seed: 42
alpha: 0.05

output:
  dir: outputs/analise
```

## Estrutura de Saída

| Arquivo | Conteúdo |
|---|---|
| `diagnostico_painel.csv` | Balanço, unidades, períodos, lacunas |
| `diagnostico_pesos.csv` | Diagnóstico das matrizes de pesos |
| `coeficientes.csv` | Coeficientes de todos os modelos |
| `comparacao_modelos.csv` | Comparação de R², parâmetro espacial |
| `notas_identificacao.csv` | Limites de identificação causal |
| `relatorio.md` | Relatório Markdown completo |
| `manifesto.json` | Proveniência (inputs, outputs, seed) |

## Limites de Identificação Causal

- **Efeitos fixos (within)**: identifica efeitos within-unit, não elimina variáveis
  omitidas variantes no tempo correlacionadas com os preditores.
- **Lag espacial (IV/2SLS)**: ρ identificado sob exogeneidade de W e validade dos
  instrumentos (WX, W²X). Interpretação causal requer tratamento explícito de
  endogeneidade.
- **Erro espacial (GM)**: λ corrige eficiência, não consistência dos βs. Interpretação
  causal dos βs requer exogeneidade condicional.
- **Modelo dinâmico**: viés de Nickell em painéis curtos. Para inferência válida,
  use estimadores de Arellano-Bond (não implementados aqui).
