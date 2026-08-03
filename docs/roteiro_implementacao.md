# Roteiro de implementação das aplicações do curso

Este roteiro converte o programa de **Análise Territorial e Econometria Espacial** em uma sequência de aplicações computacionais reproduzíveis. Ele parte da auditoria registrada em [`inventario_aplicacoes.md`](inventario_aplicacoes.md): somente o ciclo de aprendizado de máquina espacial v0.1–v0.4 foi localizado como aplicação executável; os demais laboratórios precisam ser desenvolvidos ou incorporados caso arquivos anteriores venham a ser encontrados.

## Princípios comuns

Cada aplicação deverá:

1. declarar objetivo didático, pergunta analítica e limites de inferência;
2. utilizar somente software e bibliotecas de código aberto;
3. separar dados brutos, dados processados, código e resultados;
4. registrar origem, licença, versão e hash dos dados;
5. oferecer execução por linha de comando e, quando útil, notebook comentado;
6. funcionar com uma configuração reduzida para testes;
7. registrar sementes, versões do ambiente e parâmetros efetivos;
8. possuir testes automatizados para operações críticas;
9. produzir tabelas e figuras regeneráveis, sem resultados fixados manualmente;
10. distinguir exploração, predição, estimação e inferência causal.

## Arquitetura prevista

```text
applications/
├── dados_espaciais/
├── autocorrelacao_espacial/
├── diagnostico_ols/
├── econometria_espacial/
├── maup_sensibilidade/
├── heterogeneidade_espacial/
├── paineis_espaciais/
├── redes_acessibilidade/
└── ml_espacial/

templates/
└── projeto_aplicado/
```

A existência de um caminho neste roteiro não significa que o módulo esteja pronto. O status oficial permanece no inventário e nas issues do repositório.

## Onda 1 — Fundamentos computacionais

### A1. Dados espaciais, projeções, junções e cartografia

**Objetivo:** construir uma base territorial documentada e demonstrar como sistemas de referência, geometrias inválidas, chaves de junção e escolhas cartográficas afetam os resultados.

**Produtos mínimos:**

- rotina de aquisição ou geração da base de demonstração;
- validação de esquema e geometria;
- transformação de CRS com justificativa;
- junção tabular e espacial;
- indicadores de completude e duplicidade;
- mapa coroplético reproduzível;
- relatório de procedência;
- testes de integridade.

**Dependências:** nenhuma aplicação anterior.

### A2. Matrizes de pesos e autocorrelação global/local

**Objetivo:** comparar contiguidade queen/rook, k-vizinhos e distância; calcular Moran global, Geary, Moran local e Getis-Ord; testar sensibilidade à matriz e ao tratamento de ilhas.

**Produtos mínimos:**

- construtores de pesos;
- diagnóstico de conectividade e ilhas;
- permutações com semente registrada;
- tabelas comparativas;
- mapas de significância e clusters;
- correção ou discussão de múltiplas comparações;
- testes numéricos e de invariância.

**Dependência:** A1.

## Onda 2 — Econometria espacial

### A3. OLS e diagnóstico espacial

**Objetivo:** estimar linha de base OLS, verificar heterocedasticidade, multicolinearidade, influência e autocorrelação dos resíduos, sem selecionar automaticamente um modelo espacial apenas pela significância dos testes.

**Produtos mínimos:**

- especificação OLS declarada;
- diagnóstico residual;
- Moran dos resíduos sob matrizes alternativas;
- testes LM quando metodologicamente adequados;
- comparação entre erros convencionais e robustos;
- relatório de limitações.

**Dependência:** A2.

### A4. SAR, SEM, SLX e SDM

**Objetivo:** comparar mecanismos espaciais alternativos, interpretar efeitos diretos, indiretos e totais e demonstrar que coeficientes autorregressivos não devem ser lidos como coeficientes OLS.

**Produtos mínimos:**

- estimação de SAR, SEM, SLX e SDM;
- justificativa substantiva da matriz;
- decomposição dos impactos;
- comparação de ajuste e resíduos;
- sensibilidade a matrizes alternativas;
- checagem de convergência e estabilidade;
- testes com dados simulados de parâmetros conhecidos.

**Dependência:** A3.

## Onda 3 — Escala e heterogeneidade

### A5. MAUP e sensibilidade territorial

**Objetivo:** demonstrar como escala e zoneamento alteram estatísticas descritivas, autocorrelação e coeficientes, separando efeitos de agregação de diferenças substantivas.

**Produtos mínimos:**

- ao menos três esquemas de agregação;
- tabela de variação dos resultados;
- mapas comparáveis;
- análise de estabilidade de sinais, magnitudes e significância;
- registro das perdas de informação.

**Dependência:** A1–A4, conforme o ensaio escolhido.

### A6. GWR e MGWR

**Objetivo:** explorar relações espacialmente variáveis, comparar bandas e escalas e explicitar riscos de colinearidade local, múltiplas estimativas e interpretação causal indevida.

**Produtos mínimos:**

- seleção documentada de banda;
- comparação entre modelo global, GWR e MGWR;
- superfícies de coeficientes e incerteza;
- diagnóstico de colinearidade local;
- testes de estabilidade por reamostragem ou perturbação.

**Dependência:** A3 e A5.

## Onda 4 — Tempo, redes e integração

### A7. Painéis espaciais

**Objetivo:** organizar dados município–tempo, distinguir efeitos fixos espaciais e temporais e comparar especificações estáticas e, quando viável, dinâmicas.

**Produtos mínimos:**

- validação da estrutura do painel;
- tratamento explícito de lacunas;
- matriz espacial estável ou justificação de mudança temporal;
- comparação entre modelos não espaciais e espaciais;
- interpretação de efeitos e limites da identificação.

**Dependência:** A4.

### A8. Redes, acessibilidade e fluxos

**Objetivo:** calcular indicador territorial de acessibilidade ou centralidade em rede, distinguindo distância euclidiana, distância em rede, oportunidades e impedância.

**Produtos mínimos:**

- aquisição/documentação da rede;
- validação topológica;
- cálculo de caminhos e acessibilidade;
- análise de sensibilidade à função de impedância;
- mapa e tabela de desigualdades territoriais;
- discussão do contexto geográfico incerto.

**Dependência:** A1; integração opcional com A2 e A5.

### A9. Template do projeto aplicado

**Objetivo:** oferecer uma estrutura mínima para problema, dados, método, validação, resultados, limitações e reprodução.

**Produtos mínimos:**

- arquivo de configuração;
- manifesto de dados;
- caderno ou relatório reproduzível;
- estrutura de testes;
- checklist de revisão;
- exemplo de execução com uma das aplicações incorporadas.

**Dependência:** ao menos A1–A4 concluídas.

## Critérios de conclusão por aplicação

Uma aplicação somente poderá receber status `incorporada` quando:

- a documentação permitir execução por terceiro;
- os dados forem obtidos por rotina documentada ou substituíveis por fixture licenciada;
- os testes passarem localmente e no CI;
- não houver vazamento entre etapas analíticas;
- os resultados forem regeneráveis;
- as limitações estiverem explicitadas;
- a ligação com o encontro e o produto do curso estiver registrada.

## Prioridade imediata

A próxima aplicação deve ser **A1 — Dados espaciais, projeções, junções e cartografia**, porque todas as demais dependem da qualidade da base geográfica e das decisões de representação territorial.
