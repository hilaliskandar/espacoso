# Piloto de Aprendizado de Máquina Espacial — v0.4

Implementação executável do **Protocolo de Ensaio Reprodutível — Aprendizado de Máquina Espacial**.

## Objetivo

Comparar modelos não espaciais e espaciais sob desenhos de validação compatíveis com interpolação e transferência territorial, evitando vazamento entre treinamento e teste.

## Modelos

- **M0**: regressão Ridge não espacial;
- **M1**: random forest não espacial;
- **M2U**: random forest com defasagens de covariáveis por k vizinhos e pesos uniformes;
- **M2D**: random forest com defasagens de covariáveis por distância inversa;
- **M3**: random forest com base espectral espacial derivada de kernel RBF centrado e extensão fora da amostra.

M2U e M2D não utilizam a variável-alvo para construir atributos. Para observações de teste, os vizinhos pertencem exclusivamente ao treinamento da dobra.

## Aplicação territorial real v0.4

A versão 0.4 incorpora um benchmark autocontido com 175 unidades nacionais derivadas do Natural Earth em escala 1:110m. O alvo é o logaritmo do PIB estimado; os atributos substantivos incluem população, área, perímetro, compacidade e continente. As geometrias são transformadas para EPSG:6933 antes do cálculo de centroides e medidas.

A execução principal é:

```bash
python -m src.run_experiment --config config/experimento_natural_earth_v0_4.yml
```

A base deve ser regenerada localmente e não é versionada no repositório.

## Validação

O benchmark real compara:

1. K-fold aleatório;
2. blocos espaciais finos;
3. blocos espaciais agregados com buffer de 500 km.

O ajuste de hiperparâmetros, a calibração dos intervalos e a geração de atributos espaciais ocorrem dentro das dobras de treinamento.

## Instalação

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

No Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## Testes

```bash
pytest -q
```

## Produtos

Cada execução gera métricas, previsões, busca de hiperparâmetros, Moran global, LISA, intervalos, mapas, tabela de otimismo, decisão dos gates, manifesto, configuração efetiva e log.

## Limitações

- O benchmark Natural Earth é pequeno e agregado em escala nacional; não representa mercado habitacional nem permite inferência causal.
- PIB e população são estimativas incorporadas à versão vetorial distribuída, não séries econômicas atuais.
- Distâncias, buffers e centroides são aproximações em projeção global equivalente.
- M3 não reproduz integralmente todas as variantes de Moran eigenvector maps ou ESF.
- Os intervalos usam quantis de resíduos de validação interna e constituem aproximação cross-conformal pragmática.
- A classificação LISA é diagnóstica e depende da matriz, do número de vizinhos, do nível de significância e das permutações.

## Resultado resumido

M0 apresentou o menor RMSE mediano na validação aleatória, espacial fina e espacial agregada com buffer. Os modelos espaciais reduziram parte do Moran residual, mas elevaram o erro e alargaram os intervalos. O resultado reforça que complexidade espacial adicional deve ser justificada por validação territorial, não apenas por melhora de diagnóstico residual.
