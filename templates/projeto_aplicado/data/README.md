# Manifesto de dados e ambiente

Este documento registra a procedência dos dados, as licenças e o ambiente
de execução. Preencha antes de compartilhar ou submeter o projeto.

## Dados brutos

| Campo | Valor |
|---|---|
| Nome do arquivo | `raw/TODO.gpkg` |
| Fonte | _[nome da fonte, URL]_ |
| Licença | _[CC BY 4.0 / IBGE / etc.]_ |
| Data de acesso | _[AAAA-MM-DD]_ |
| Versão ou release | _[v1.0 / 2022 / etc.]_ |
| Hash SHA-256 | _[preencher com `sha256sum arquivo`]_ |
| CRS original | _[EPSG:XXXX]_ |

### Esquema esperado

| Coluna | Tipo | Descrição |
|---|---|---|
| `id` | texto | Identificador único da unidade territorial |
| `indicador` | numérico | Variável dependente do estudo |
| `geometry` | Polygon/MultiPolygon | Geometria da unidade |

### Instrução de obtenção

```bash
# TODO: substitua pelo comando ou URL de download real
# wget -O data/raw/base.gpkg "https://..."
# ou
# Acesse <URL> e salve em data/raw/
```

## Dados derivados

Os arquivos em `processed/` e `outputs/` são gerados pela pipeline. Não os
versione no repositório. Gere-os localmente com `make run`.

## Fixture sintética para testes

`tests/fixtures/` contém uma malha sintética mínima gerada pelo próprio
repositório (veja `scripts/create_demo_data.py`). Ela é distribuível porque
não representa território real e foi gerada internamente.

## Ambiente de execução

Preencha após a execução final:

```
Python: TODO
Sistema operacional: TODO
Data: TODO
```

Lista completa de pacotes:

```
TODO: cole aqui a saída de `python -m pip freeze`
```

## Hashes dos resultados

| Arquivo | SHA-256 |
|---|---|
| `outputs/manifesto.json` | _[hash]_ |
| `outputs/estimacao/coeficientes.csv` | _[hash]_ |

## Notas sobre licenças

- Dados do IBGE: domínio público com atribuição obrigatória.
- Demais fontes: verifique individualmente.
- Código: GPL-3.0-or-later (veja `../LICENSE`).
- Este template: CC BY 4.0.
