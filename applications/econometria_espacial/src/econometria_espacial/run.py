"""CLI entry point para econometria_espacial."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="econometria-espacial",
        description="Estima SAR, SEM, SLX, SDM e decompõe impactos espaciais.",
    )
    parser.add_argument(
        "--config",
        required=True,
        type=Path,
        help="Caminho para o arquivo de configuração YAML.",
    )
    args = parser.parse_args(argv)

    # Import tardio para não pesar no tempo de startup
    from .pipeline import run_pipeline

    print(f"[econometria-espacial] Carregando configuração: {args.config}")
    outputs = run_pipeline(args.config)
    print(f"[econometria-espacial] Concluído. {len(outputs)} arquivo(s) gerado(s):")
    for p in outputs:
        print(f"  {p}")


if __name__ == "__main__":
    main()
