from __future__ import annotations

import argparse

from .pipeline import run_pipeline


def main() -> None:
    parser = argparse.ArgumentParser(description="Executa análise de painéis espaciais.")
    parser.add_argument("config", help="Caminho para o arquivo YAML de configuração.")
    args = parser.parse_args()
    outputs = run_pipeline(args.config)
    print(f"Execução concluída: {len(outputs)} produtos.")
    for path in outputs:
        print(path)


if __name__ == "__main__":
    main()
