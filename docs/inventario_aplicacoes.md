# Inventário de aplicações computacionais do curso

Este documento controla a localização, verificação e incorporação das aplicações já produzidas para o curso de Análise Territorial e Econometria Espacial.

A presença de um tema nesta tabela **não significa que o respectivo código já tenha sido localizado**. O status somente deve mudar após inspeção dos arquivos originais, execução local e verificação de licença, dados e dependências.

| Bloco | Aplicação candidata | Ferramentas possíveis | Status | Evidência/localização | Próxima ação |
|---|---|---|---|---|---|
| 1 | Preparação e exploração de dados espaciais | QGIS, Python, R | a verificar | — | localizar arquivos e cadernos |
| 2 | Matrizes de pesos e autocorrelação espacial | GeoDa, PySAL, R | a verificar | — | localizar arquivos e cadernos |
| 3 | Regressão linear e diagnóstico espacial | Python, R, GeoDa | a verificar | — | localizar arquivos e cadernos |
| 4 | Modelos econométricos espaciais | PySAL, R | a verificar | — | localizar arquivos e cadernos |
| 5 | Heterogeneidade, escala e/ou dados em painel | R, Python | a verificar | — | confrontar com o programa do curso |
| 6 | Aprendizado de máquina e validação espacial | Python | incorporada | `applications/ml_espacial/` | evoluir para benchmark subnacional |

## Critérios de verificação

Para cada item localizado, registrar:

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

- `a verificar`: há previsão temática, mas o código ainda não foi inspecionado;
- `localizada`: os arquivos foram encontrados, sem validação completa;
- `em revisão`: dependências, dados e resultados estão sendo testados;
- `incorporada`: código documentado, executável e testado no repositório;
- `histórica`: preservada para auditoria, mas substituída por versão posterior;
- `não incorporável`: arquivo incompleto, irreprodutível ou incompatível com licença/dados.
