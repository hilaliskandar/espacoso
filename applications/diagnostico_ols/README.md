# A3 — OLS e diagnóstico espacial

Aplicação didática e reproduzível do curso **Análise Territorial e Econometria Espacial**.

## Objetivo

Construir uma linha de base OLS antes da estimação de modelos espaciais e demonstrar como especificação, heterocedasticidade, multicolinearidade, influência e dependência residual devem ser avaliadas em conjunto.

A aplicação **não seleciona automaticamente** SAR, SEM, SLX ou SDM. Os testes espaciais são diagnósticos condicionais à especificação OLS e à matriz de pesos.

## Conteúdo

- OLS com erros-padrão convencionais e robustos HC0–HC3;
- VIF e número de condição;
- resíduos, alavancagem, distância de Cook, resíduos studentizados e DFFITS;
- Breusch–Pagan, White, Jarque–Bera e Durbin–Watson;
- Moran dos resíduos com permutações;
- LM-error, LM-lag, LM robustos e LM-SARMA;
- comparação entre especificações e matrizes de pesos;
- mapas de resíduos e influência;
- GeoPackage, tabelas, relatório e manifesto com hashes.

## Demonstração

A fixture gera uma grade 8 × 8 com processo conhecido:

```text
y = 5 + 2*x1 - 1.5*x2 + 4.0*z_spatial + erro heterocedástico
```

O modelo `baseline` omite `z_spatial`; o modelo `expanded` a inclui. A comparação demonstra como uma variável espacialmente estruturada omitida pode produzir viés e autocorrelação residual.

## Execução

```bash
python -m pip install --upgrade pip setuptools wheel
python -m pip install -e .[dev]
python scripts/create_demo_data.py --output-dir data/demo
diagnostico-ols config/demo.yml
python -m pytest -q
```

## Entradas

A aplicação espera:

1. arquivo espacial validado, preferencialmente produzido pela A1;
2. arquivos de arestas das matrizes, preferencialmente produzidos pela A2;
3. YAML com modelos, matrizes, sementes e diretório de saída.

## Produtos

- `coeficientes.csv`;
- `resumo_modelos.csv`;
- `diagnosticos_classicos.csv`;
- `diagnosticos_espaciais.csv`;
- `vif.csv`;
- `influencia.csv`;
- `diagnostico_pesos.csv`;
- `diagnostico_ols.gpkg`;
- mapas de resíduos e influência;
- `relatorio.md`;
- `manifesto.json`.

## Limites

- HC3 não corrige especificação incorreta; apenas ajusta a matriz de covariância.
- VIF não determina mecanicamente a exclusão de variáveis.
- Observações influentes devem ser investigadas, não removidas automaticamente.
- Moran residual e testes LM dependem da matriz de pesos.
- Significância espacial residual não demonstra causalidade.
- A escolha e interpretação de modelos espaciais será aprofundada na A4.
