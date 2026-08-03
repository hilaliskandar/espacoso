# Resultados do benchmark territorial real — v0.4

## Base e desenho

O ensaio utiliza 175 unidades nacionais derivadas do Natural Earth em escala 1:110m. Antártida e a categoria “Seven seas (open ocean)” foram excluídas. O alvo é `log1p(gdp_md_est)`. As covariáveis são log da população, log da área, log do perímetro, compacidade e indicadores continentais. Centroides, área e perímetro são calculados em EPSG:6933.

Foram executadas duas repetições independentes, cada uma com três dobras externas e validação interna aninhada. Os desenhos externos são:

1. aleatório;
2. espacial fino, com grade 4 × 4;
3. espacial agregado, com grade 3 × 3 e buffer de 500 km.

## RMSE mediano

| Modelo | Aleatória | Espacial fina | Agregada + buffer |
|---|---:|---:|---:|
| M0 — Ridge | 0,9728 | **0,9922** | **0,9490** |
| M1 — RF | 1,0841 | 1,0644 | 1,0393 |
| M2U — RF + lags uniformes | 1,0592 | 1,1498 | 1,1840 |
| M3 — RF + base espectral | 1,0307 | 1,0600 | 1,2369 |

M0 apresenta o menor RMSE mediano nos três desenhos. Os modelos espaciais reduzem parte da autocorrelação residual, mas não compensam a perda de desempenho preditivo.

## Dependência espacial residual

| Modelo | Moran mediano — espacial fina | Moran mediano — agregada + buffer |
|---|---:|---:|
| M0 | 0,4049 | 0,2617 |
| M1 | 0,2880 | 0,1111 |
| M2U | 0,2726 | 0,1032 |
| M3 | **0,2142** | 0,1756 |

O ensaio revela uma tensão entre minimizar erro fora da amostra e retirar estrutura espacial dos resíduos; nenhum modelo domina simultaneamente os dois critérios.

## Gates

- Gate 0 — dados: aprovado.
- Gate 1 — ausência de vazamento: aprovado pelos 15 testes.
- Gate 2 — validade das partições: aprovado para os três desenhos.
- Gate 3 — desempenho espacial: reprovado.
- Gate 4 — resíduos: reprovado.
- Gate 5 — incerteza: aprovado quanto à cobertura global, com ressalva de intervalos largos.
- Gate 6 — robustez: parcialmente aprovado.
- Gate 7 — reprodutibilidade: aprovado no pacote original; no GitHub, depende da conclusão da migração integral do código e dos scripts.

## Conclusão

O benchmark real não sustenta a superioridade dos modelos espaciais testados. A regressão Ridge é mais simples, mais precisa e produz intervalos mais estreitos. As representações espaciais reduzem parte da autocorrelação residual, mas não o suficiente para compensar a perda preditiva.

O desenvolvimento seguinte deve usar unidades subnacionais, maior tamanho amostral, covariáveis substantivas e um comparador econométrico espacial.
