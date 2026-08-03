# Inventário auditado de aplicações computacionais do curso

Este documento controla a localização, verificação, incorporação e desenvolvimento das aplicações do curso de **Análise Territorial e Econometria Espacial**.

## Resultado da auditoria inicial

A auditoria foi realizada em 3 de agosto de 2026 a partir de:

- aba **Roteiro do curso** da [planilha bibliográfica](https://docs.google.com/spreadsheets/d/11vUrMRVqhl8Tjprm1WaO006mRTbp4DlDPQivfdyHqQE/edit);
- campos `Material operacional`, `Pacote executável` e `Caderno de implementação` da planilha;
- histórico de produção do curso;
- busca no Google Drive por pacotes, notebooks e scripts;
- conteúdo já incorporado ao repositório.

O roteiro contém onze etapas formativas e treze exercícios descritos como laboratórios. Entretanto, somente a etapa 10 — aprendizado de máquina espacial, validação e endogeneidade — possui pacotes executáveis e cadernos de implementação efetivamente vinculados. Não foram localizados notebooks `.ipynb`, scripts Python ou scripts R correspondentes às demais etapas.

Essa conclusão significa **“não localizado nas fontes inspecionadas”**, e não prova de que os arquivos jamais tenham existido. Caso sejam encontrados posteriormente, deverão ser avaliados pelos critérios deste inventário antes da incorporação.

## Matriz de situação

| Etapa | Conteúdo e produto previsto | Natureza computacional | Situação auditada | Evidência | Destino proposto |
|---:|---|---|---|---|---|
| 1 | Território, escala, dependência e heterogeneidade — nota conceitual | predominantemente conceitual | sem aplicação autônoma prevista | roteiro, linha 1 | documentação em `docs/`; sem pacote próprio |
| 2 | Dados espaciais, projeções, joins e cartografia — base geográfica documentada | laboratório de preparação de dados | código não localizado | campos operacionais vazios | `applications/dados_espaciais/` |
| 3 | Pesos espaciais, Moran global e LISA — diagnóstico exploratório | laboratório analítico | código não localizado | campos operacionais vazios | `applications/autocorrelacao_espacial/` |
| 4 | OLS, resíduos e testes espaciais — comparação OLS × diagnóstico | laboratório econométrico inicial | código não localizado | campos operacionais vazios | `applications/diagnostico_ols/` |
| 5 | SAR, SEM, SLX e SDM — modelos e impactos | laboratório econométrico espacial | código não localizado | campos operacionais vazios | `applications/econometria_espacial/` |
| 6 | MAUP, falácia ecológica e sensibilidade — ensaio de robustez | laboratório de sensibilidade territorial | código não localizado | campos operacionais vazios | `applications/maup_sensibilidade/` |
| 7 | GWR, MGWR e heterogeneidade — análise local crítica | laboratório de heterogeneidade | código não localizado | campos operacionais vazios | `applications/heterogeneidade_espacial/` |
| 8 | Painéis espaciais — exercício longitudinal | laboratório espaço-temporal | código não localizado | campos operacionais vazios | `applications/paineis_espaciais/` |
| 9 | Redes, acessibilidade e fluxos — indicador territorial | laboratório de redes e acessibilidade | código não localizado | campos operacionais vazios | `applications/redes_acessibilidade/` |
| 10 | Aprendizado de máquina espacial, validação e endogeneidade — benchmark preditivo | aplicação completa | **incorporada e testada** | pacotes v0.1–v0.4; 15 testes | [`applications/ml_espacial/`](../applications/ml_espacial/) |
| 11 | Estudo aplicado — relatório reproduzível | integração dos módulos | template/código não localizado | campos operacionais vazios | `templates/projeto_aplicado/` após os módulos básicos |

## Laboratórios identificados no programa detalhado

O programa descreve exercícios nos encontros 2 a 10 e 12 a 15:

1. comparação de indicador em diferentes escalas;
2. preparação de base espacial;
3. cartografia analítica;
4. comparação de matrizes de pesos;
5. Moran global;
6. LISA e Getis-Ord;
7. OLS e diagnóstico dos resíduos;
8. SAR e SEM;
9. SLX, SDM e impactos;
10. GWR e MGWR;
11. painel espacial;
12. acessibilidade, segregação ou redes;
13. validação espacial e aprendizado de máquina.

Para reduzir duplicação, os treze exercícios serão organizados em oito aplicações modulares, conforme a matriz de situação. A aplicação de aprendizado de máquina já ocupa uma dessas frentes.

## Ordem recomendada de incorporação

A ordem não deve seguir a sofisticação algorítmica, mas as dependências pedagógicas:

1. dados espaciais, projeções, joins e cartografia;
2. matrizes de pesos e autocorrelação global/local;
3. OLS e diagnóstico espacial;
4. SAR, SEM, SLX, SDM e impactos;
5. MAUP e sensibilidade territorial;
6. GWR/MGWR e heterogeneidade;
7. painéis espaciais;
8. redes e acessibilidade;
9. template do estudo aplicado.

O módulo de aprendizado de máquina permanece como aplicação avançada e referência de padrões de reprodutibilidade.

## Critérios de verificação e incorporação

Para cada item localizado ou desenvolvido, registrar:

1. arquivo original e data da última modificação;
2. finalidade didática e encontro/módulo correspondente;
3. linguagem, bibliotecas e versão do ambiente;
4. origem, licença e condições de redistribuição dos dados;
5. possibilidade de execução offline;
6. presença de resultados fixados manualmente;
7. riscos de vazamento, erro espacial ou inferência indevida;
8. testes existentes e testes ainda necessários;
9. decisão: incorporar, refatorar, arquivar como histórico ou descartar;
10. caminho definitivo no repositório.

## Estados permitidos

- `não localizado`: previsto no programa, sem arquivo executável encontrado;
- `localizado`: arquivos encontrados, ainda sem validação completa;
- `em revisão`: dependências, dados e resultados em teste;
- `em desenvolvimento`: código novo necessário porque não foi localizado material prévio;
- `incorporado`: código documentado, executável e testado no repositório;
- `histórico`: preservado para auditoria, mas substituído por versão posterior;
- `não incorporável`: arquivo incompleto, irreprodutível ou incompatível com licença/dados.
