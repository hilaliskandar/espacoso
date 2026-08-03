# Dados

Os dados brutos e os produtos processados não são versionados.

A base demonstrativa é sintética e pode ser criada com:

```bash
python scripts/create_demo_data.py --output data/raw
```

Ela contém nove polígonos regulares em EPSG:4326, localizados apenas para fins didáticos nas proximidades de São Paulo, e uma tabela de indicadores fictícios. Não representa unidades administrativas, população observada ou qualquer fenômeno real.

Para uma aplicação externa, o arquivo YAML deve indicar:

- arquivo espacial legível pelo GeoPandas;
- tabela CSV, Excel ou Parquet;
- chaves únicas;
- CRS de análise adequado;
- colunas numéricas;
- limiar mínimo de cobertura da junção.

Cada base externa deve ter origem, licença, versão e hash registrados.
