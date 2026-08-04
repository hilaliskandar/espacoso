# Changelog

## 0.1.0 — 2026-08-04

- fixture sintética de rede viária e unidades territoriais (grade 4 × 4 + unidade isolada);
- validação topológica com diagnóstico de componentes, nós isolados e arestas duplicadas;
- algoritmo de Dijkstra com limite de custo (max_cost);
- funções de impedância: linear, exponencial negativa, binária e lei de potência;
- cálculo de acessibilidade gravitacional (A_i = Σ O_j · f(c_ij));
- centralidade de betweenness, closeness e degree para os nós da rede;
- comparação de distância em rede vs. distância euclidiana com razão de desvio;
- tabela de desigualdades territoriais (percentis, CV, razão máx/mín, média ponderada);
- mapas coropléticos por impedância, rede e desvio;
- relatório JSON com nota sobre contexto geográfico incerto;
- manifesto de execução com hashes SHA-256;
- CLI, configuração YAML, testes e integração contínua.
