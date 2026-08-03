from pathlib import Path

import geopandas as gpd
import pandas as pd
import yaml
from shapely.geometry import box

from autocorrelacao_espacial.config import load_config
from autocorrelacao_espacial.pipeline import run_pipeline


def test_full_pipeline(tmp_path):
    gdf = gpd.GeoDataFrame(
        {
            "id": ["a", "b", "c", "d", "island"],
            "indicator": [10.0, 11.0, 20.0, 21.0, 15.0],
            "geometry": [box(0, 0, 1, 1), box(1, 0, 2, 1), box(0, 1, 1, 2), box(1, 1, 2, 2), box(10, 0, 11, 1)],
        },
        crs="EPSG:3857",
    )
    data_path = tmp_path / "input.gpkg"
    gdf.to_file(data_path, layer="territories", driver="GPKG")
    config_path = tmp_path / "config.yml"
    config_path.write_text(
        yaml.safe_dump(
            {
                "data": {
                    "path": str(data_path),
                    "layer": "territories",
                    "id_column": "id",
                    "value_column": "indicator",
                    "analysis_crs": "EPSG:3857",
                },
                "analysis": {
                    "primary_weight": "rook",
                    "permutations": 19,
                    "seed": 7,
                    "alpha": 0.05,
                    "fdr": True,
                    "weights": [
                        {"name": "rook", "type": "rook", "transform": "row_standardized"},
                        {"name": "knn1", "type": "knn", "k": 1, "transform": "row_standardized"},
                    ],
                },
                "output": {"directory": str(tmp_path / "outputs"), "maps": False},
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    result = run_pipeline(load_config(config_path), config_path)
    output = Path(result["output_dir"])
    expected = {
        "diagnostico_matrizes.csv",
        "estatisticas_globais.csv",
        "sensibilidade_matrizes.csv",
        "moran_local_rook.csv",
        "getis_ord_gstar_rook.csv",
        "resultados_matriz_principal.gpkg",
        "relatorio_autocorrelacao.json",
        "manifesto_execucao.json",
    }
    assert expected.issubset({path.name for path in output.iterdir()})
    diagnostics = pd.read_csv(output / "diagnostico_matrizes.csv")
    assert diagnostics.loc[diagnostics["name"] == "rook", "islands"].item() == 1
    assert diagnostics.loc[diagnostics["name"] == "knn1", "islands"].item() == 0
