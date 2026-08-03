# Política de dados do piloto

Os dados brutos e processados não são versionados neste repositório. Cada execução deve registrar origem, licença, versão, data de acesso e hash SHA-256.

## CSV territorial genérico

Colunas mínimas esperadas:

- coordenada horizontal;
- coordenada vertical;
- variável-alvo;
- covariáveis numéricas.

Linhas com valores ausentes nas colunas selecionadas devem ser tratadas de forma explícita e documentada.

## Benchmark Natural Earth v0.4

A preparação reproduzível deve gerar:

- `processed/natural_earth_countries_v0_4.csv`: matriz analítica numérica;
- `processed/natural_earth_country_index_v0_4.csv`: correspondência entre `row_id`, país e ISO;
- `processed/natural_earth_provenance_v0_4.json`: hashes, CRS, exclusões e transformação.

Foram excluídas Antártida e a categoria cartográfica “Seven seas (open ocean)”. O alvo é `log1p(gdp_md_est)`. As coordenadas e medidas geométricas são calculadas em EPSG:6933.

## Regra de reprodutibilidade

Um benchmark somente deve ser considerado reproduzível quando o manifesto registrar:

1. origem e licença;
2. identificador ou versão da fonte;
3. hash dos arquivos brutos e processados;
4. CRS e transformações geométricas;
5. exclusões e filtros;
6. sementes e configuração efetiva;
7. ambiente de software.
