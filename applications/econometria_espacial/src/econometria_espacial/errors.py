"""Exceções específicas da aplicação econometria_espacial."""
from __future__ import annotations


class ConfigError(ValueError):
    """Configuração inválida ou ausente."""


class WeightsError(ValueError):
    """Matriz de pesos inválida."""


class EstimationError(RuntimeError):
    """Falha na estimação do modelo."""
