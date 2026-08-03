# Espaçoso

Repositório didático e experimental do curso de **Análise Territorial e Econometria Espacial**.

O projeto concentra aplicações reproduzíveis em análise espacial, econometria espacial, validação territorial e aprendizado de máquina espacial. A documentação pedagógica, os fichamentos bibliográficos e as versões formais de entrega permanecem no Google Drive; este repositório é a fonte principal do código, dos testes e das configurações computacionais.

## Estrutura

```text
applications/       aplicações completas e pilotos reproduzíveis
notebooks/          laboratórios didáticos, organizados por módulo
src/espacoso/       componentes reutilizáveis entre aplicações
tests/              testes compartilhados
configs/            configurações gerais
docs/               documentação técnica, decisões e backlog
reports/             relatórios leves e resultados sintéticos
figures/             figuras selecionadas e reproduzíveis
data/                instruções de obtenção; dados brutos não são versionados
templates/           estruturas reutilizáveis para o projeto aplicado
```

A estrutura será preenchida progressivamente. Aplicações autocontidas permanecem em `applications/`; componentes realmente reutilizados por mais de uma aplicação poderão ser promovidos para `src/espacoso/`.

## Aplicações disponíveis

| Aplicação | Estado | Cobertura |
|---|---|---|
| [Dados espaciais, projeções, junções e cartografia](applications/dados_espaciais/README.md) | funcional e testada localmente | pipeline genérico, fixture offline, 13 testes, workflow configurado |
| [Aprendizado de máquina espacial](applications/ml_espacial/README.md) | funcional e testada | ciclo v0.1–v0.4, 15 testes, integração contínua |

A A1 valida CRS, geometrias, chaves, cobertura da junção e colunas numéricas; produz GeoPackage processado, relatório de qualidade, mapa e manifesto com hashes. O piloto de aprendizado de máquina compara modelos não espaciais e espaciais sob validação aleatória e territorial, com diagnóstico de autocorrelação residual, intervalos preditivos, rastreabilidade e gates de desempenho.

## Auditoria das demais aplicações

A inspeção do histórico, da planilha de controle e do Google Drive localizou pacotes executáveis anteriores apenas para o ciclo de aprendizado de máquina espacial. Os demais laboratórios constam do programa, mas não possuem código previamente localizado. A A1 foi, portanto, desenvolvida como aplicação nova; as etapas seguintes serão incorporadas caso os arquivos apareçam ou desenvolvidas de forma reproduzível.

Documentos de controle:

- [inventário auditado](docs/inventario_aplicacoes.md);
- [roteiro de implementação](docs/roteiro_implementacao.md);
- [backlog e issues](docs/backlog.md);
- [padrão mínimo das aplicações](docs/padrao_aplicacao.md);
- [registro da decisão de auditoria](docs/decisoes/0001-inventario-inicial.md).

A prioridade imediata passa a ser a issue [#3 — Matrizes de pesos e autocorrelação espacial](https://github.com/hilaliskandar/espacoso/issues/3), que utilizará a base validada pela A1.

## Princípios

- separação entre código, dados brutos e produtos derivados;
- ambientes e sementes explicitamente registrados;
- validação espacial sem vazamento entre treino e teste;
- métricas e gates definidos antes da interpretação dos resultados;
- testes automatizados para funções críticas;
- rastreabilidade de procedência, licença e hash dos dados;
- distinção entre demonstração didática, benchmark preditivo e inferência causal;
- preservação do histórico sem duplicação desnecessária de código obsoleto.

## Política de incorporação

Cada nova aplicação deverá conter, no mínimo:

1. objetivo e vínculo com o programa do curso;
2. código executável e configuração de exemplo;
3. instruções de ambiente e dados;
4. testes proporcionais aos riscos metodológicos;
5. manifesto de procedência e limitações;
6. resultados sintéticos ou critérios para regenerá-los;
7. licença e forma de citação compatíveis com o repositório.

## Situação

A estrutura-base está estabelecida. O ciclo de aprendizado de máquina espacial v0.1–v0.4 foi migrado, as demais aplicações foram auditadas e a A1 foi implementada e testada localmente. O workflow remoto está configurado, mas seu status ainda não foi exposto pelo conector. O próximo desenvolvimento é a aplicação A2 de pesos e autocorrelação espacial.
