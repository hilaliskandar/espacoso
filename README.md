# Espaçoso

Repositório didático e experimental do curso de **Análise Territorial e Econometria Espacial**.

O projeto concentra aplicações reproduzíveis em análise espacial, econometria espacial, validação territorial e aprendizado de máquina espacial. A documentação pedagógica, os fichamentos bibliográficos e as versões de entrega permanecem no Google Drive; este repositório é a fonte principal do código, dos testes e das configurações computacionais.

## Estrutura

```text
applications/       aplicações completas e pilotos reproduzíveis
notebooks/          laboratórios didáticos, organizados por módulo
src/espacoso/       componentes reutilizáveis do curso
tests/              testes compartilhados
configs/            configurações gerais
docs/               documentação técnica
reports/             relatórios leves e resultados sintéticos
figures/             figuras selecionadas e reproduzíveis
data/                instruções de obtenção; dados brutos não são versionados
```

## Aplicação inicial

A primeira aplicação incorporada é o **Piloto de Aprendizado de Máquina Espacial v0.4**, com modelos não espaciais e espaciais, validação aleatória e territorial, diagnóstico de autocorrelação residual e gates de desempenho.

Consulte [`applications/ml_espacial/README.md`](applications/ml_espacial/README.md).

## Princípios

- separação entre código, dados brutos e produtos derivados;
- ambientes e sementes explicitamente registrados;
- validação espacial sem vazamento entre treino e teste;
- métricas e gates definidos antes da interpretação dos resultados;
- testes automatizados para funções críticas;
- rastreabilidade de procedência, licença e hash dos dados;
- distinção entre demonstração didática, benchmark preditivo e inferência causal.

## Situação

Estrutura inicial do repositório e migração do piloto v0.4.
