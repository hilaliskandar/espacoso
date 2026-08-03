# Aprendizado de Máquina Espacial — ciclo v0.1–v0.4

Implementação executável do **Protocolo de Ensaio Reprodutível — Aprendizado de Máquina Espacial**.

A pasta contém o código consolidado mais recente e preserva a evolução metodológica das versões anteriores por configurações históricas e pelo [`CHANGELOG.md`](CHANGELOG.md). Não são mantidas quatro cópias integrais do mesmo código.

## Objetivo

Comparar modelos não espaciais e espaciais sob desenhos de validação compatíveis com interpolação e transferência territorial, evitando vazamento entre treinamento e teste.

## Evolução

| Versão | Avanço principal | Testes de referência |
|---|---|---:|
| v0.1 | M0–M3, validação aleatória/espacial e Moran global | 5 |
| v0.2 | validação aninhada, múltiplas escalas, buffer, LISA, intervalos e gates | 12 |
| v0.3 | CSV territorial offline, repetição de partições e manifesto ampliado | 14 |
| v0.4 | benchmark territorial real, procedência e hashes | 15 |

## Modelos

- **M0**: regressão Ridge não espacial;
- **M1**: random forest não espacial;
- **M2U**: random forest com defasagens de covariáveis por k vizinhos e pesos uniformes;
- **M2D**: random forest com defasagens de covariáveis por distância inversa;
- **M3**: random forest com base espectral espacial derivada de kernel RBF centrado e extensão fora da amostra.

M2U e M2D não utilizam a variável-alvo para construir atributos. Para observações de teste, os vizinhos pertencem exclusivamente ao treinamento da dobra. A base espectral do M3 também é ajustada apenas nas coordenadas do conjunto de treinamento.

## Estrutura

```text
config/       configurações históricas e atuais
src/          núcleo do pipeline
scripts/      preparação de dados, consolidação e cartografia
tests/        testes unitários, de integração e de contrato
data/         política de dados e manifesto de procedência
outputs/      produtos locais; não versionados
```

## Instalação

```bash
cd applications/ml_espacial
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Para preparar dados vetoriais e produzir mapas coropléticos:

```bash
python -m pip install -r requirements-geo.txt
```

No Windows PowerShell:

```powershell
cd applications/ml_espacial
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## Testes

```bash
python -m pytest -q
```

Estado verificado da migração: **15 testes aprovados**. O mesmo comando é executado pelo GitHub Actions.

## Execuções por versão

```bash
make run-v01
make run-v02
make run-v03
```

O benchmark v0.4 depende da base processada local:

```bash
python scripts/prepare_natural_earth.py
make run-v04
```

Também é possível executar diretamente qualquer configuração:

```bash
python -m src.run_experiment --config config/experimento_sintetico_v0_3.yml
```

## Aplicação territorial real v0.4

A versão 0.4 utiliza 175 unidades nacionais derivadas do Natural Earth em escala 1:110m. O alvo é o logaritmo do PIB estimado; os atributos incluem população, área, perímetro, compacidade e continente. As geometrias são transformadas para EPSG:6933 antes do cálculo de centroides e medidas.

O benchmark compara:

1. K-fold aleatório;
2. blocos espaciais finos;
3. blocos espaciais agregados com buffer de 500 km.

Ajuste de hiperparâmetros, calibração dos intervalos e geração de atributos espaciais ocorrem dentro das dobras de treinamento.

Os dados brutos e os CSVs derivados não são versionados. O repositório mantém o script de preparação e o manifesto com origem, transformações esperadas e hashes de referência. O teste de contrato confere o manifesto e, quando os CSVs estão presentes, verifica sua integridade.

## Produtos

Cada execução pode gerar:

- métricas e previsões fora da amostra;
- busca de hiperparâmetros;
- Moran global e local/LISA;
- intervalos preditivos;
- mapas de resíduos e clusters;
- tabela de otimismo entre validação aleatória e espacial;
- decisões dos gates;
- configuração efetiva, manifesto e log.

## Resultado resumido da v0.4

M0 apresentou o menor RMSE mediano na validação aleatória, espacial fina e espacial agregada com buffer. Os modelos espaciais reduziram parte do Moran residual, mas elevaram o erro e alargaram os intervalos. A complexidade espacial adicional, portanto, não foi justificada pelo desempenho preditivo neste benchmark.

Consulte [`RESULTADOS_v0_4.md`](RESULTADOS_v0_4.md).

## Limitações

- O benchmark Natural Earth é pequeno e agregado em escala nacional; não representa mercado habitacional nem permite inferência causal.
- PIB e população são estimativas incorporadas à versão vetorial utilizada no experimento, não séries econômicas atuais.
- Distâncias, buffers e centroides são aproximações em projeção global equivalente.
- M3 não reproduz integralmente todas as variantes de Moran eigenvector maps ou ESF.
- Os intervalos usam quantis de resíduos de validação interna e constituem aproximação cross-conformal pragmática.
- A classificação LISA é diagnóstica e depende da matriz, do número de vizinhos, do nível de significância e das permutações.

## Desenvolvimento seguinte

O próximo benchmark deverá empregar unidades subnacionais, maior tamanho amostral, covariáveis substantivas e ao menos um comparador econométrico espacial.