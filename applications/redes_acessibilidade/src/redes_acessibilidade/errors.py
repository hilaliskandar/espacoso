"""Erros específicos da aplicação de redes e acessibilidade."""
from __future__ import annotations


class ConfigError(ValueError):
    """Erro de configuração."""


class TopologyError(ValueError):
    """Erro topológico na rede."""


class NetworkError(ValueError):
    """Erro na construção ou análise da rede."""
