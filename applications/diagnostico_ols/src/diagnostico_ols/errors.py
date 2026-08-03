class DiagnosticoOLSError(Exception):
    """Erro-base da aplicação."""


class ConfigError(DiagnosticoOLSError):
    """Configuração inválida."""


class DataError(DiagnosticoOLSError):
    """Dados incompatíveis com o contrato."""


class WeightsError(DiagnosticoOLSError):
    """Matriz de pesos inválida ou desalinhada."""
