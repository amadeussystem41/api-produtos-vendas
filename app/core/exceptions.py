"""Exceções de negócio da aplicação."""

from typing import ClassVar


class APIError(Exception):
    """Exceção base para erros de negócio tratados pela API."""

    status_code: ClassVar[int] = 400

    def __init__(self, mensagem: str) -> None:
        self.mensagem = mensagem
        super().__init__(mensagem)


class RecursoNaoEncontradoError(APIError):
    """Recurso solicitado não existe."""

    status_code = 404


class ConflitoDeDadosError(APIError):
    """Operação conflita com o estado atual dos dados."""

    status_code = 409


class EstoqueInsuficienteError(ConflitoDeDadosError):
    """Não há quantidade suficiente em estoque para concluir a venda."""
