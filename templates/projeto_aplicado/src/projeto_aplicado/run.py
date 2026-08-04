"""Ponto de entrada do projeto aplicado.

Execute via:
    python -m projeto_aplicado.run --config config/projeto.yml
ou
    make run
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Executa o projeto aplicado reproduzível."
    )
    parser.add_argument(
        "--config",
        required=True,
        type=Path,
        help="Caminho para o arquivo YAML de configuração",
    )
    args = parser.parse_args(argv)

    from projeto_aplicado.config import load_config

    cfg = load_config(args.config)
    print(f"[projeto_aplicado] Configuração carregada: {args.config}")
    print(f"[projeto_aplicado] Projeto: {cfg['projeto']['titulo']}")
    print(
        "[projeto_aplicado] Adapte src/projeto_aplicado/run.py para a sua análise."
    )

    # TODO: substitua este bloco pela pipeline real do estudo
    # Exemplo:
    # from projeto_aplicado.pipeline import run_pipeline
    # run_pipeline(cfg)

    return 0


if __name__ == "__main__":
    sys.exit(main())
