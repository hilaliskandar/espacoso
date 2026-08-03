# A2 — Matrizes de pesos e autocorrelação espacial

Aplicação didática e reproduzível do curso **Análise Territorial e Econometria Espacial**.

## Objetivo

Construir, diagnosticar e comparar matrizes de pesos espaciais e demonstrar como a definição de vizinhança altera Moran I, Geary C, Moran local e Getis-Ord G*.

A aplicação não seleciona automaticamente uma matriz “correta”. Cada matriz representa uma hipótese sobre interação territorial e deve ser justificada pelo problema substantivo.

## Matrizes disponíveis

- contiguidade **rook**;
- contiguidade **queen**;
- **k-vizinhos mais próximos**, com simetrização por união, mutualidade ou sem simetrização;
- **banda de distância**, binária ou ponderada por distância inversa;
- pesos binários ou padronizados por linha.

## Produtos

Cada execução gera:

- listas de arestas para cada matriz;
- diagnóstico de ilhas, componentes e cardinalidades;
- Moran I e Geary C com permutações;
- Moran local com clusters `HH`, `LL`, `HL`, `LH`, `NS` e `Island`;
- Getis-Ord G* com classes `Hot`, `Cold` e `NS`;
- p-valores e q-valores de Benjamini-Hochberg;
- mapas por matriz;
- tabela comparativa de sensibilidade;
- GeoPackage com resultados da matriz principal;
- relatório e manifesto de execução com hashes.

## Demonstração

```bash
python -m pip install --no-build-isolation -e .
python scripts/create_demo_data.py
python -m autocorrelacao_espacial.run --config config/demo.yml
```

Ou:

```bash
make install
make run
```

A fixture sintética contém uma malha 4 × 4 e uma unidade territorial isolada. Ela permite conferir diferenças entre contiguidade, distância e k-vizinhos sem depender de rede ou dados externos.

## Testes

```bash
python -m pytest -q
```

Os testes verificam alinhamento, simetrização, ilhas, componentes, transformação por linha, estatísticas globais conhecidas, testes locais, FDR e execução integral.

## Decisões metodológicas

- as observações são ordenadas pela chave antes da construção dos pesos;
- matrizes de distância exigem CRS projetado;
- rook exige interseção de fronteira com comprimento positivo;
- queen aceita qualquer contato de fronteira;
- ilhas permanecem com linha de pesos nula e são explicitamente classificadas;
- Moran local usa permutação condicional simplificada por unidade;
- Getis-Ord G* inclui a própria unidade com peso 1;
- a significância local usa q-valores quando `fdr: true`;
- resultados locais são exploratórios e não constituem inferência causal.

## Limitações

- a construção de contiguidade é pareada e prioriza transparência, não desempenho em bases muito grandes;
- a tolerância de fronteira pode afetar rook em geometrias com erros topológicos;
- a simetrização de k-vizinhos modifica cardinalidades;
- testes locais dependem da matriz, da padronização, do número de permutações e da correção para múltiplas comparações;
- clusters e hot spots não demonstram mecanismos causais;
- a malha sintética serve apenas para teste e ensino.
