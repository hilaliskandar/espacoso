class DadosEspaciaisError(Exception):
    """Erro-base da aplicação."""


class ConfigError(DadosEspaciaisError):
    """Configuração ausente ou inválida."""


class DataContractError(DadosEspaciaisError):
    """Violação do contrato dos dados de entrada."""
