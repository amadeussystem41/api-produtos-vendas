"""Schemas de entrada e saída de vendas."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.venda import StatusVenda
from app.schemas.comum import PaginacaoBase


class ItemVendaCriar(BaseModel):
    """Produto e quantidade que serão incluídos na venda."""

    produto_id: int = Field(gt=0, examples=[1], description="Identificador do produto.")
    quantidade: int = Field(
        gt=0,
        le=1_000_000,
        examples=[2],
        description="Quantidade vendida do produto.",
    )


class VendaCriar(BaseModel):
    """Dados necessários para registrar uma venda."""

    itens: list[ItemVendaCriar] = Field(
        min_length=1,
        max_length=100,
        description="Ao menos um item deve ser informado.",
    )
    observacao: str | None = Field(
        default=None,
        max_length=500,
        examples=["Venda realizada no balcão da loja."],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "itens": [
                    {"produto_id": 1, "quantidade": 2},
                    {"produto_id": 2, "quantidade": 1},
                ],
                "observacao": "Venda realizada no balcão da loja.",
            }
        }
    )


class ItemVendaResposta(BaseModel):
    """Item da venda com os dados preservados no momento da compra."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    produto_id: int
    nome_produto: str
    quantidade: int
    preco_unitario: Decimal
    subtotal: Decimal


class VendaResposta(BaseModel):
    """Representação completa de uma venda."""

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "data_venda": "2026-01-15T14:00:00",
                "total": 649.70,
                "status": "CONCLUIDA",
                "observacao": "Venda realizada no balcão da loja.",
                "cancelada_em": None,
                "itens": [
                    {
                        "id": 1,
                        "produto_id": 1,
                        "nome_produto": "Teclado Mecânico RGB",
                        "quantidade": 2,
                        "preco_unitario": 249.90,
                        "subtotal": 499.80,
                    }
                ],
            }
        },
    )

    id: int
    data_venda: datetime
    total: Decimal
    status: StatusVenda
    observacao: str | None
    cancelada_em: datetime | None
    itens: list[ItemVendaResposta]


class PaginaVendas(PaginacaoBase):
    """Página do histórico de vendas."""

    itens: list[VendaResposta]
