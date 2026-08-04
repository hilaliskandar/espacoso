# A8 — Redes, acessibilidade e fluxos territoriais

Aplicação didática e reproduzível do curso **Análise Territorial e Econometria Espacial**.

## Objetivo

Modelar redes espaciais e calcular acessibilidade gravitacional, distinguindo distância euclidiana, distância em rede, oportunidades, impedância e fluxos observados.

A aplicação não seleciona automaticamente uma função de impedância "correta". Cada função representa uma hipótese sobre o comportamento de deslocamento e deve ser justificada pelo problema substantivo.

## Conceitos fundamentais

| Conceito | Definição |
|---|---|
| **Distância euclidiana** | Menor distância entre dois pontos no espaço métrico (linha reta) |
| **Distância em rede** | Comprimento do caminho mínimo entre dois nós na rede |
| **Razão de desvio** | Distância em rede / distância euclidiana (≥ 1) |
| **Oportunidades** | Quantidade de destinos relevantes (empregos, serviços, etc.) em cada unidade |
| **Impedância** | Função que penaliza oportunidades conforme o custo de acesso |
| **Acessibilidade** | Soma ponderada de oportunidades: A_i = Σ_j O_j · f(c_ij) |

## Funções de impedância disponíveis

- **linear**: f(c) = max(0, 1 − c/cutoff) — decaimento linear até o limiar
- **negative_exponential**: f(c) = exp(−β·c) — decaimento exponencial (parâmetro β)
- **binary**: f(c) = 1 se c ≤ cutoff, 0 caso contrário — potencial cumulativo
- **power**: f(c) = 1/(1+c)^p — decaimento por lei de potência

## Medidas de centralidade

- **betweenness** — intermediação: frequência com que um nó aparece nos caminhos mínimos
- **closeness** — proximidade: inverso da distância média a todos os nós
- **degree** — grau: número normalizado de conexões diretas

## Produtos

Cada execução gera:

- `origens_acessibilidade.gpkg` — unidades com colunas de acessibilidade por impedância;
- `relatorio_topologia.json` — diagnóstico de arestas, nós, componentes e isolados;
- `comparacao_rede_euclidiana.csv` — razão de desvio entre pares de origens;
- `tabela_desigualdades.csv` — percentis, CV e razão máx/mín por impedância;
- `centralidade_nos.csv` — centralidade dos nós da rede (quando configurado);
- `caminhos_minimos_origens.csv` — custo mínimo em rede entre pares de origens;
- mapas PNG por impedância, rede, comparação e desvio (opcional);
- `relatorio_acessibilidade.json` — resumo com nota sobre contexto geográfico incerto;
- `manifesto_execucao.json` — hashes SHA-256 de todas as saídas.

## Demonstração

```bash
python -m pip install --no-build-isolation -e .
python scripts/create_demo_data.py
python -m redes_acessibilidade.run --config config/demo.yml
```

Ou:

```bash
make install
make run
```

A fixture sintética contém uma grade 4 × 4 de segmentos viários e 17 unidades territoriais, incluindo uma unidade isolada sem conexão na rede. Ela permite:

- diagnosticar componentes desconectados;
- comparar impedância linear com exponencial negativa;
- visualizar desigualdades territoriais de acessibilidade;
- verificar que a razão de desvio é sempre ≥ 1.

## Testes

```bash
python -m pytest -q
```

Os testes verificam:

- validação de configuração (impedâncias, campos obrigatórios, duplicatas);
- topologia (componentes, nós isolados, simetria da adjacência);
- algoritmo de Dijkstra (caminhos mínimos, max_cost, inalcançável);
- centralidade de grau;
- funções de impedância (valores limítrofes, monotonicidade, fórmulas);
- acessibilidade gravitacional (ordenação relativa);
- razão de desvio rede/euclidiana (≥ 1);
- pipeline completo (todos os produtos, colunas de acessibilidade, manifesto).

## Decisões metodológicas

- a rede é tratada como não-dirigida (ida e volta com mesmo custo);
- cada unidade de origem é atribuída ao nó da rede mais próximo por distância euclidiana;
- a acessibilidade usa as mesmas unidades como origens e destinos (auto-acessibilidade excluída);
- oportunidades nulas ou negativas são ignoradas no cálculo;
- unidades isoladas (fora do componente principal) têm acessibilidade zero para destinos inalcançáveis;
- centralidade é calculada sobre todos os nós da rede, não apenas sobre os snap points.

## Limitações e contexto geográfico incerto

- a construção de nós por tolerância de snap pode criar pseudo-interseções em cruzamentos reais não modelados;
- sentidos de circulação, semáforos, curvas de velocidade e impedâncias reais de travessia não são modelados;
- o algoritmo de snap de origens usa o nó mais próximo em linha reta, não o ponto de acesso mais lógico;
- centralidade de intermediação tem custo O(n³) e não é recomendada para redes com > 500 nós sem otimização;
- a acessibilidade gravitacional é sensível ao parâmetro de impedância — a discussão do valor de β deve ser fundamentada empiricamente;
- clusters de alta/baixa acessibilidade não demonstram mecanismos causais.
