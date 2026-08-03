class AutocorrelacaoError(Exception):
    """Erro-base da aplicação."""


class ConfigError(AutocorrelacaoError):
    """Configuração inválida."""


class DataError(AutocorrelacaoError):
    """Dados incompatíveis com o contrato da aplicação."""


class WeightsError(AutocorrelacaoError):
    """Matriz de pesos inválida ou impossível de construir."""
