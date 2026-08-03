# Decisão 0001 — Inventário inicial das aplicações

**Data:** 2026-08-03  
**Situação:** aceita

## Contexto

O programa do curso descreve laboratórios em dados espaciais, cartografia, pesos, autocorrelação, econometria espacial, escala, heterogeneidade, painéis, redes e aprendizado de máquina.

A inspeção do histórico, da planilha de controle, da pasta de trabalho no Google Drive e das buscas por `.py`, `.R` e `.ipynb` encontrou pacotes executáveis apenas para a linha de aprendizado de máquina espacial v0.1–v0.4.

## Decisão

1. O ciclo v0.1–v0.4 será tratado como uma única aplicação evolutiva consolidada.
2. Os demais temas serão registrados como aplicações previstas, mas **não localizadas**.
3. Nenhum laboratório será apresentado como implementado com base apenas em sua descrição no programa.
4. Arquivos posteriormente encontrados serão inspecionados antes de serem incorporados.
5. Na ausência de código anterior, serão desenvolvidas novas aplicações seguindo `docs/padrao_aplicacao.md`.

## Consequências

- o inventário diferencia previsão pedagógica e implementação comprovada;
- a ordem de desenvolvimento começa por dados espaciais;
- issues do GitHub controlam cada aplicação;
- o módulo ML funciona como referência de testes, manifestos e reprodutibilidade, sem impor sua arquitetura a problemas de natureza distinta.
