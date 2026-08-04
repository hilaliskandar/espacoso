# MAUP e Sensibilidade Territorial

Ensaio reproduzível sobre os **efeitos de escala e zoneamento** (*Modifiable Areal Unit Problem*) na estatística descritiva, autocorrelação espacial e estimação de modelos.

## Estrutura

```
maup_sensibilidade/
├── config/          # Configurações YAML
├── data/            # Dados de entrada (não versionados)
├── outputs/         # Saídas geradas (não versionadas)
├── scripts/         # Scripts auxiliares
├── src/
│   └── maup_sensibilidade/
│       ├── aggregation.py   # Rotinas de agregação territorial
│       ├── cartography.py   # Mapas coropléticos comparativos
│       ├── config.py        # Carregamento e validação de configuração
│       ├── errors.py        # Exceções do domínio
│       ├── io.py            # Leitura/escrita de geodados
│       ├── pipeline.py      # Orquestrador principal
│       ├── reporting.py     # Relatório Markdown e manifesto JSON
│       ├── run.py           # Ponto de entrada CLI
│       └── statistics.py    # Moran I, descritivas, tabela de estabilidade
└── tests/
```

## Instalação

```bash
pip install -e ".[dev]"
```

## Uso

```bash
# Gerar dados de demonstração
python scripts/create_demo_data.py --output-dir data/demo

# Executar análise
maup-sensibilidade config/demo.yml
```

ou via Make:

```bash
make install
make run
```

## Produtos

- Arquivos GeoPackage com agregados por esquema territorial;
- `estatisticas_descritivas.csv` — médias, dispersão por esquema;
- `estabilidade_moran.csv` — I de Moran, sinal, magnitude e significância por esquema;
- `conservacao_totais.csv` — testes de conservação de totais;
- Mapas PNG com classes compatíveis entre esquemas;
- `relatorio.md` — discussão sobre perda de informação e falácia ecológica;
- `manifesto.json` — auditoria determinística (semente, hash dos insumos).

## Critérios de Aceite

- Agregações auditáveis e determinísticas (semente fixa, manifesto com hash);
- Denominadores e ponderações explicitados na configuração YAML;
- Diferenças entre esquemas atribuídas com cautela (tabela de estabilidade);
- Testes de conservação de totais automáticos;
- CI aprovado.
