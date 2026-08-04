# Checklist de revisão metodológica

Use este checklist antes de submeter o projeto aplicado. Marque cada item
como ✅ (aprovado), ❌ (reprovado/pendente) ou N/A (não se aplica).

---

## 1. Reprodutibilidade

- [ ] O projeto executa do zero com `make install && make demo-data && make run`
- [ ] Os testes passam com `make test`
- [ ] O manifesto `outputs/manifesto.json` foi gerado e contém hashes, versões e data
- [ ] A semente aleatória está fixada no YAML de configuração
- [ ] O ambiente foi documentado em `data/README.md`
- [ ] Reprodução verificada por um terceiro (nome: ________________ / data: _______)

## 2. Separação analítica

Marque qual estratégia o projeto utiliza e confirme a adequação:

- [ ] **Análise exploratória** — os mapas e estatísticas descrevem, não inferem
- [ ] **Estimação** — parâmetros interpretados com incerteza e condicionais ao modelo
- [ ] **Predição** — desempenho avaliado fora da amostra com validação espacial
- [ ] **Causalidade** — desenho quasi-experimental justificado e pressupostos discutidos

Marque os itens de separação:

- [ ] Análise exploratória é apresentada antes da estimação/predição
- [ ] O estudo não confunde parâmetros estimados com efeitos causais (se não há desenho causal)
- [ ] O estudo não confunde ajuste in-sample com capacidade preditiva (se houver predição)
- [ ] Inferência causal não é afirmada quando o desenho é apenas associativo

## 3. Dados

- [ ] Fonte, licença e data de acesso registrados em `data/README.md`
- [ ] Hash SHA-256 do(s) arquivo(s) bruto(s) registrado(s)
- [ ] Dados brutos não versionados no repositório (apenas fixtures sintéticas)
- [ ] CRS de análise documentado e justificado
- [ ] Variável dependente e covariáveis descritas e suas distribuições verificadas
- [ ] Valores ausentes tratados e documentados

## 4. Modelo e especificação

- [ ] Pergunta analítica traduzida em especificação formal
- [ ] Escolha do modelo justificada (não apenas pela significância de testes)
- [ ] Diagnósticos de especificação realizados (resíduos, multicolinearidade, heterocedasticidade)
- [ ] Autocorrelação espacial dos resíduos verificada após estimação
- [ ] Sensibilidade à matriz de pesos discutida (quando aplicável)
- [ ] Sensibilidade à especificação (inclusão/exclusão de variáveis) discutida

## 5. Validação preditiva (se aplicável)

- [ ] Validação cruzada espacial (block CV ou buffer CV) utilizada
- [ ] Vazamento entre treino e teste descartado
- [ ] Moran dos resíduos de teste calculado
- [ ] Métricas reportadas por dobra (não apenas a média)

## 6. Comunicação cartográfica

- [ ] Todo mapa tem título, escala gráfica, seta norte e fonte
- [ ] CRS indicado na figura ou legenda
- [ ] Paleta acessível a daltônicos (ColorBrewer ou equivalente)
- [ ] Número de classes e método de classificação justificados
- [ ] Legenda completa, sem omissão de categorias
- [ ] Mapas de cluster distinguem significância estatística de magnitude

## 7. Comunicação estatística

- [ ] Intervalos de confiança ou erro-padrão reportados para estimativas centrais
- [ ] P-valores não são a única informação comunicada
- [ ] Tamanho de efeito e relevância prática discutidos
- [ ] Limitações da inferência baseada em permutações descritas (quando aplicável)
- [ ] Múltiplos testes corrigidos (FDR/Bonferroni) quando pertinente

## 8. Limitações e usos indevidos

- [ ] Limitações do estudo listadas no README e no relatório
- [ ] Usos indevidos a evitar explicitados
- [ ] Generalizações externas ao recorte analisado não são afirmadas
- [ ] MAUP e falácia ecológica considerados quando a unidade é agregada

## 9. Integridade e boas práticas

- [ ] Código segue convenções do projeto (PEP 8 / ruff)
- [ ] Sem credenciais, tokens ou dados pessoais no repositório
- [ ] Licenças dos dados compatíveis com a redistribuição pública
- [ ] Citações de pacotes e dados incluídas no relatório

---

**Data de revisão:** _______________  
**Revisado por:** _______________  
**Resultado:** ☐ Aprovado ☐ Aprovado com ressalvas ☐ Reprovado
