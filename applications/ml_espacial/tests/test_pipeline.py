from pathlib import Path

import pandas as pd

from src.run_experiment import run


def test_full_smoke_pipeline(tmp_path):
    config = Path("config/experimento_sintetico_v0_2.yml")
    text = config.read_text(encoding="utf-8")
    text = text.replace("sample_limit: 240", "sample_limit: 90")
    text = text.replace("n_estimators_grid: [24]", "n_estimators_grid: [8]")
    text = text.replace(
        "output_dir: outputs/synthetic_v0_2", f"output_dir: {tmp_path.as_posix()}"
    )
    local_config = tmp_path / "config.yml"
    local_config.write_text(text, encoding="utf-8")
    run(local_config)
    required = [
        "metrics.csv",
        "predictions.csv",
        "hyperparameter_search.csv",
        "local_moran.csv",
        "optimism.csv",
        "gates.json",
        "manifest.json",
        "summary.csv",
    ]
    for name in required:
        assert (tmp_path / name).exists()
    metrics = pd.read_csv(tmp_path / "metrics.csv")
    assert set(metrics["model"]) == {"M0", "M1", "M2U", "M2D", "M3"}
    assert set(metrics["validation"]) == {
        "random",
        "spatial_fine",
        "spatial_coarse_buffered",
    }
