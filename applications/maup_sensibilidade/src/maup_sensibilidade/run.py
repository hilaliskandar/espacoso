from __future__ import annotations

"""Ponto de entrada da linha de comando."""

import argparse
import sys
from pathlib import Path

from .pipeline import run_pipeline


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Análise MAUP — sensibilidade territorial"
    )
    parser.add_argument("config", help="Caminho para o arquivo de configuração YAML")
    args = parser.parse_args()
    outputs = run_pipeline(Path(args.config))
    for p in outputs:
        print(p)


if __name__ == "__main__":
    sys.exit(main())
