"""Schemas comuns de resposta e paginação."""

from pydantic import BaseModel, Field


class MensagemResposta(BaseModel):
    """Mensagem simples de retorno."""

    mensagem: str = Field(examples=["Operação realizada com sucesso."])


class ErroResposta(BaseModel):
    """Formato padrão de erro da API."""

    detail: str = Field(examples=["Produto não encontrado."])


class PaginacaoBase(BaseModel):
    """Metadados de paginação compartilhados pelos endpoints de listagem."""

    total: int = Field(ge=0, description="Quantidade total de registros encontrados.")
    skip: int = Field(ge=0, description="Registros ignorados no início da consulta.")
    limit: int = Field(ge=1, description="Quantidade máxima de registros retornados.")
