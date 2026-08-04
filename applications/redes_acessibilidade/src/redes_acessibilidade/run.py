"""CLI da aplicação de redes e acessibilidade."""
from __future__ import annotations

import argparse

from .pipeline import run_pipeline


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Calcula acessibilidade em rede, centralidade e fluxos territoriais."
    )
    parser.add_argument("--config", required=True, help="Caminho do arquivo YAML de configuração.")
    args = parser.parse_args()
    result = run_pipeline(args.config)
    print(f"Saídas em: {result['output_dir']}")
    for path in result["outputs"]:
        print(f"  {path}")


if __name__ == "__main__":
    main()
