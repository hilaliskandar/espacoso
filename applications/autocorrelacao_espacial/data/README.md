# Política de dados da A2

A aplicação não versiona bases territoriais reais nem produtos derivados.

A demonstração usa uma malha sintética de 16 polígonos contíguos e uma unidade isolada, criada por `scripts/create_demo_data.py`. A malha é distribuível porque é gerada integralmente pelo próprio repositório e não representa território real.

Para usar uma base externa:

1. execute previamente a A1 para corrigir geometrias, CRS, chaves e junções;
2. aponte `data.path` para um arquivo vetorial local;
3. registre origem, licença, data, versão e hash fora ou dentro de um manifesto apropriado;
4. não envie dados restritos ou arquivos volumosos ao GitHub.
