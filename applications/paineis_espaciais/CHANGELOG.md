# Changelog — paineis_espaciais

## [0.1.0] — 2026-08-04

### Adicionado
- Módulo `panel.py`: construção de painel com índice (unidade, tempo) único e ordenado,
  diagnóstico de balanço, tratamento de lacunas sem contaminação entre unidades,
  defasagens temporais seguras.
- Módulo `weights.py`: construção e diagnóstico de matrizes de pesos espaciais;
  suporte a matrizes constantes e variáveis no tempo.
- Módulo `models.py`: efeitos fixos (within OLS), lag espacial (IV/2SLS) e erro
  espacial (GM iterativo); modelo dinâmico com aviso sobre limites de identificação.
- Módulo `config.py`: carregamento e validação de configuração YAML.
- Módulo `io.py`: leitura de dados CSV e GeoPackage; escrita de tabelas.
- Módulo `reporting.py`: relatório Markdown e manifesto JSON de proveniência.
- Módulo `pipeline.py`: orquestração completa dos produtos de análise.
- CLI `paineis-espaciais` via `run.py`.
- Testes unitários e de integração com painel simulado.
- Script `scripts/create_demo_data.py` para dados de demonstração.
- Configuração `config/demo.yml`.
- Notebook `notebooks/A7_paineis_espaciais.ipynb`.
- CI `/.github/workflows/paineis-espaciais.yml`.
