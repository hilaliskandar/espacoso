# A1 — Dados espaciais, projeções, junções e cartografia

Aplicação-base do curso de **Análise Territorial e Econometria Espacial**. O módulo demonstra que a qualidade da análise depende de decisões anteriores à modelagem: CRS, validade das geometrias, unicidade das chaves, cobertura da junção e classificação cartográfica.

## Objetivo didático

Ao final, deve ser possível:

- inspecionar um arquivo espacial e sua tabela de atributos;
- distinguir CRS declarado e CRS adequado à análise;
- detectar e reparar geometrias inválidas;
- validar chaves e realizar junção um-para-um;
- medir cobertura e identificar chaves sem correspondência;
- produzir mapa e relatório regeneráveis;
- registrar procedência, versões e hashes.

## Instalação

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --no-build-isolation -e ".[test]"
```

No PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --no-build-isolation -e ".[test]"
```

## Execução demonstrativa

```bash
make run
```

Ou:

```bash
python scripts/create_demo_data.py --output data/raw
PYTHONPATH=src python -m dados_espaciais.run --config config/demo.yml
```

Os produtos são escritos em `outputs/demo/`:

- `territorios_processados.gpkg`;
- `relatorio_qualidade.json`;
- `chaves_espaciais_sem_correspondencia.csv`;
- `chaves_tabulares_nao_utilizadas.csv`;
- `mapa_indicador.png`;
- `manifesto_execucao.json`.

## Configuração externa

O pipeline aceita arquivo espacial, CSV/Excel/Parquet e YAML próprio. A aplicação não pressupõe que coordenadas geográficas sejam adequadas a área ou distância: o CRS de análise é obrigatório.

## Testes

```bash
PYTHONPATH=src python -m pytest -q
```

A bateria cobre contrato da configuração, chaves duplicadas, CRS ausente, reparo de geometria, cobertura da junção, classificação cartográfica e execução integral.

## Limitações

- a rotina não decide automaticamente qual CRS é substantivamente adequado;
- `make_valid` pode alterar o tipo ou a composição da geometria;
- uma junção completa não demonstra compatibilidade conceitual entre unidades e indicadores;
- quantis e intervalos iguais produzem narrativas cartográficas distintas;
- a fixture demonstrativa é sintética e não pode sustentar conclusões territoriais.

## Relação com o curso

A aplicação atende aos laboratórios de preparação de base espacial e cartografia analítica e constitui dependência para pesos espaciais, autocorrelação e econometria espacial.
