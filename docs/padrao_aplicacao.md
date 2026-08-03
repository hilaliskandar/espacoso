# Padrão mínimo para aplicações computacionais

Toda aplicação do Espaçoso deve adotar, salvo justificativa explícita, a seguinte estrutura:

```text
applications/<nome>/
├── README.md
├── CHANGELOG.md
├── CITATION.cff
├── requirements.txt ou environment.yml
├── Makefile
├── config/
├── data/
│   ├── README.md
│   ├── raw/.gitkeep opcional
│   └── processed/.gitkeep opcional
├── notebooks/
├── scripts/
├── src/
├── tests/
└── reports/
```

## README obrigatório

O README deve informar:

- encontro ou etapa do curso;
- objetivo didático;
- pergunta analítica;
- dados e licença;
- instalação;
- comandos de preparação, teste e execução;
- produtos gerados;
- interpretação dos resultados;
- limitações e usos indevidos a evitar.

## Configuração

Parâmetros metodológicos devem permanecer em YAML, TOML ou JSON versionado, incluindo:

- sementes;
- variáveis;
- CRS;
- matriz de pesos;
- número de permutações;
- partições;
- modelos;
- limiares e gates.

## Dados

Dados brutos e derivados volumosos não devem ser versionados. O repositório deve conter:

- rotina de obtenção ou instrução precisa;
- licença e fonte;
- hash quando aplicável;
- esquema esperado;
- fixture mínima licenciada ou sintética para testes.

## Testes mínimos

Cada aplicação deve testar:

1. contrato dos dados;
2. determinismo sob semente fixa;
3. operação espacial crítica;
4. ausência de sobreposição ou vazamento quando houver validação;
5. consistência dimensional e de índices;
6. caso sintético com resultado conhecido;
7. geração dos produtos essenciais.

## Resultados

Tabelas, mapas e relatórios devem ser regeneráveis. Resultados publicados devem registrar:

- commit;
- configuração efetiva;
- versões do ambiente;
- hashes dos dados;
- data da execução;
- avisos e limitações.

## Linguagem e ferramentas

Python ou R podem ser utilizados. QGIS e GeoDa podem integrar o percurso didático, mas operações centrais devem possuir uma forma documentada de reprodução por código sempre que tecnicamente possível.
