from __future__ import annotations


class ConfigError(ValueError):
    """Configuração inválida ou incompleta."""


class DataError(ValueError):
    """Dado de entrada inválido ou corrompido."""


class AggregationError(RuntimeError):
    """Falha durante a agregação territorial."""
