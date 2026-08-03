from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import pandas as pd

from .errors import DataContractError


def load_spatial(path: Path) -> gpd.GeoDataFrame:
    if not path.exists():
        raise DataContractError(f"Arquivo espacial não encontrado: {path}")
    frame = gpd.read_file(path)
    if frame.empty:
        raise DataContractError("O arquivo espacial não contém registros.")
    if frame.crs is None:
        raise DataContractError("O arquivo espacial não possui CRS declarado.")
    return frame


def load_table(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise DataContractError(f"Tabela não encontrada: {path}")
    suffix = path.suffix.lower()
    if suffix == ".csv":
        frame = pd.read_csv(path)
    elif suffix in {".xlsx", ".xls"}:
        frame = pd.read_excel(path)
    elif suffix == ".parquet":
        frame = pd.read_parquet(path)
    else:
        raise DataContractError(f"Formato tabular não suportado: {suffix}")
    if frame.empty:
        raise DataContractError("A tabela não contém registros.")
    return frame
