from __future__ import annotations

import argparse
import json
from pathlib import Path

from .config import load_config
from .pipeline import run_pipeline


def main() -> None:
    parser = argparse.ArgumentParser(description="Executa a aplicação A2 de autocorrelação espacial.")
    parser.add_argument("--config", required=True, help="Caminho para o arquivo YAML.")
    args = parser.parse_args()
    config_path = Path(args.config).resolve()
    result = run_pipeline(load_config(config_path), config_path)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
