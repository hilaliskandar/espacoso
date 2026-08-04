# A11 — Projeto Aplicado Reproduzível

Template integrador do curso **Análise Territorial e Econometria Espacial**.

Use este template para documentar, executar e comunicar um estudo aplicado completo. Cada seção contém instruções entre `<!-- ... -->` que devem ser substituídas pelo conteúdo real do projeto.

## Identificação

<!-- Substitua os campos abaixo -->

- **Título:** _[título do estudo]_
- **Participante(s):** _[nome(s)]_
- **Orientador(a):** _[nome]_
- **Encontro/etapa:** A11 — Estudo Aplicado
- **Data de entrega:** _[AAAA-MM-DD]_
- **Versão:** 0.1.0

## Problema e pergunta analítica

<!-- Descreva o problema substantivo, a unidade de análise, a escala e a
     pergunta analítica central. Seja preciso: o que se quer medir, para
     qual população, em qual período e por quê isso importa. -->

## Dados

| Campo | Valor |
|---|---|
| Fonte | _[nome e URL da fonte]_ |
| Licença | _[CC BY 4.0 / GPL / etc.]_ |
| Cobertura temporal | _[AAAA ou AAAA–AAAA]_ |
| Resolução espacial | _[município / setor censitário / etc.]_ |
| CRS original | _[EPSG:XXXX]_ |
| CRS de análise | _[EPSG:XXXX]_ |
| Hash SHA-256 | _[hash do arquivo raw]_ |

O manifesto completo de procedência está em [`data/README.md`](data/README.md).

## Método

<!-- Descreva, em no máximo dois parágrafos, a estratégia analítica:
     - qual módulo do curso é aplicado (A2–A10);
     - como a pergunta foi operacionalizada;
     - as decisões metodológicas centrais e sua justificativa substantiva. -->

### Análise exploratória

<!-- Descreva as etapas de EDA: distribuição, mapas, autocorrelação espacial. -->

### Estimação / Predição / Causalidade

<!-- Marque o que se aplica e desenvolva. -->

- [ ] Estimação de parâmetros (OLS, SAR, SEM, SLX, SDM, GWR/MGWR, painel)
- [ ] Predição fora da amostra com validação espacial
- [ ] Análise de causalidade (diferenças em diferenças, variável instrumental, etc.)

## Instalação e reprodução

```bash
# 1. Criar e ativar ambiente
python -m venv .venv
source .venv/bin/activate          # Linux/macOS
# .venv\Scripts\Activate.ps1       # Windows PowerShell

# 2. Instalar dependências
python -m pip install --upgrade pip setuptools wheel
python -m pip install -e .

# 3. Gerar dados de demonstração
make demo-data

# 4. Executar análise
make run

# 5. Executar testes
make test
```

Reprodução verificada por terceiro: <!-- nome / data -->

## Produtos gerados

| Arquivo | Descrição |
|---|---|
| `outputs/eda/` | Mapas exploratórios e diagnósticos |
| `outputs/estimacao/` | Tabelas de coeficientes e diagnósticos |
| `outputs/validacao/` | Métricas de validação e mapas de resíduo |
| `outputs/manifesto.json` | Versões, hashes e configuração efetiva |
| `reports/relatorio.md` | Relatório narrativo |
| `reports/checklist.md` | Checklist de revisão preenchido |

## Validação

<!-- Descreva os critérios de validação usados:
     - métricas de ajuste;
     - validação cruzada espacial (quando preditivo);
     - testes de robustez/sensibilidade;
     - por que os resultados são credíveis. -->

## Resultados principais

<!-- Resuma os achados centrais em dois ou três parágrafos.
     Inclua tabela ou mapa de referência se pertinente. -->

## Limitações e usos indevidos a evitar

<!-- Liste honestamente as restrições do estudo:
     - qualidade dos dados;
     - limitações do modelo;
     - escala e generalizações indevidas;
     - inferências causais que os dados não suportam. -->

## Comunicação cartográfica

<!-- Confirme que os mapas seguem os padrões do curso:
     - título, escala gráfica, norte, fonte, CRS;
     - paleta acessível a daltônicos;
     - número de classes e método de classificação justificados;
     - legenda completa e não enganosa. -->

## Ambiente de execução

O ambiente foi fixado em [`data/README.md`](data/README.md) e no manifesto gerado pela execução.

```bash
python --version
python -m pip freeze
```

## Referências

<!-- Liste as referências bibliográficas e os pacotes citados. -->

## Licença

Código: GPL-3.0-or-later.  
Dados: ver `data/README.md`.  
Relatório e materiais didáticos: CC BY 4.0 (verifique a licença original de cada fonte).
