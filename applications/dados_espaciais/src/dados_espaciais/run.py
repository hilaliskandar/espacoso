from __future__ import annotations

import argparse

from .pipeline import run_pipeline


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Valida, junta e cartografa dados territoriais."
    )
    parser.add_argument("--config", required=True, help="Caminho do arquivo YAML.")
    args = parser.parse_args()
    outputs = run_pipeline(args.config)
    for name, path in outputs.items():
        print(f"{name}: {path}")


if __name__ == "__main__":
    main()
