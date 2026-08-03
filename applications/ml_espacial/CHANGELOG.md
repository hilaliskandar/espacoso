# Histórico do piloto de aprendizado de máquina espacial

## 0.4.0 — 2026-08-03

- primeira aplicação integral a uma base territorial real autocontida;
- incorpora polígonos nacionais Natural Earth 1:110m e arquivos-fonte com hashes;
- prepara 175 unidades nacionais em projeção equivalente EPSG:6933;
- usa log do PIB estimado como alvo e população, área, perímetro, compacidade e continente como atributos;
- adiciona validação aleatória, espacial fina e espacial agregada com buffer de 500 km;
- registra automaticamente o SHA-256 do arquivo de dados no manifesto;
- torna os rótulos cartográficos genéricos para coordenadas projetadas;
- adiciona teste de integridade do benchmark e da proveniência;
- totaliza 15 testes automatizados aprovados.

## 0.3.0 — 2026-08-03

- adiciona carregador offline genérico para CSV espacial real;
- valida esquema, alvo e coordenadas numéricas;
- permite repetição configurável das partições externas;
- adiciona configuração para California Housing em CSV local;
- registra as repetições no manifesto;
- totaliza 14 testes automatizados aprovados;
- conclui ensaio sintético repetido de controle.

## 0.2.0 — 2026-08-03

- adiciona validação aninhada;
- adiciona blocos espaciais em duas escalas e buffer;
- implementa lags uniformes e por distância inversa;
- adiciona base espectral espacial com projeção fora da amostra;
- calcula Moran global para duas matrizes;
- calcula Moran local/LISA;
- gera intervalos preditivos por resíduos de validação interna;
- gera mapas de resíduos e LISA;
- produz tabela de otimismo e decisão automatizada dos gates;
- totaliza 12 testes automatizados aprovados.

## 0.1.0 — 2026-08-03

- primeira implementação com M0–M3;
- validação aleatória e espacial;
- métricas preditivas e Moran global;
- ensaio sintético;
- cinco testes automatizados aprovados.

## Política de preservação

A linha principal mantém o código consolidado mais recente. As versões anteriores são preservadas por este histórico e pelas configurações correspondentes, evitando duplicação integral de código obsoleto.