from __future__ import annotations

"""Leitura e escrita de dados de painel."""

from pathlib import Path

import pandas as pd

from .config import PanelConfig
from .errors import PanelError


def read_panel_data(config: PanelConfig) -> pd.DataFrame:
    """Lê os dados de painel do arquivo configurado.

    Suporta CSV e GeoPackage (apenas atributos tabulares são usados;
    a geometria é descartada para a análise de painel).

    Parameters
    ----------
    config:
        :class:`~paineis_espaciais.config.PanelConfig`.

    Returns
    -------
    pd.DataFrame
    """
    path = config.input_path
    if not path.exists():
        raise PanelError(f"Arquivo de dados não encontrado: {path}")

    suffix = path.suffix.lower()
    if suffix == ".csv":
        df = pd.read_csv(path)
    elif suffix in (".gpkg", ".geojson", ".shp"):
        try:
            import geopandas as gpd
        except ImportError as exc:
            raise PanelError("geopandas é necessário para ler arquivos geoespaciais.") from exc
        layer = config.geometry_layer
        gdf = gpd.read_file(path, layer=layer) if layer else gpd.read_file(path)
        df = pd.DataFrame(gdf.drop(columns="geometry", errors="ignore"))
    else:
        raise PanelError(f"Formato de arquivo não suportado: {suffix}")

    for col in (config.unit_col, config.time_col):
        if col not in df.columns:
            raise PanelError(f"Coluna obrigatória ausente nos dados: {col}")

    return df


def write_table(df: pd.DataFrame, path: Path) -> None:
    """Escreve DataFrame como CSV."""
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
