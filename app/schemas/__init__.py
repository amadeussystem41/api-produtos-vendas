"""Schemas Pydantic da API."""

from app.schemas.comum import ErroResposta, MensagemResposta, PaginacaoBase
from app.schemas.produto import (
    PaginaProdutos,
    ProdutoAtualizar,
    ProdutoBase,
    ProdutoCriar,
    ProdutoResposta,
)
from app.schemas.venda import (
    ItemVendaCriar,
    ItemVendaResposta,
    PaginaVendas,
    VendaCriar,
    VendaResposta,
)

__all__ = [
    "ErroResposta",
    "MensagemResposta",
    "PaginacaoBase",
    "ProdutoBase",
    "ProdutoCriar",
    "ProdutoAtualizar",
    "ProdutoResposta",
    "PaginaProdutos",
    "ItemVendaCriar",
    "ItemVendaResposta",
    "VendaCriar",
    "VendaResposta",
    "PaginaVendas",
]
