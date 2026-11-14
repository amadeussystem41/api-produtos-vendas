"""Modelo ORM de produto."""

from datetime import datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.venda import ItemVenda


def agora_utc() -> datetime:
    """Retorna a data/hora atual em UTC, sem timezone (compatível com SQLite)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Produto(Base):
    """Representa um produto disponível para venda."""

    __tablename__ = "produtos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    descricao: Mapped[str | None] = mapped_column(Text, nullable=True)
    categoria: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    sku: Mapped[str] = mapped_column(
        String(50), nullable=False, unique=True, index=True
    )
    preco: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    quantidade_estoque: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    ativo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=agora_utc
    )
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=agora_utc, onupdate=agora_utc
    )

    itens_venda: Mapped[list["ItemVenda"]] = relationship(back_populates="produto")

    def __repr__(self) -> str:  # pragma: no cover - helper de depuração
        return f"<Produto id={self.id} sku={self.sku!r} estoque={self.quantidade_estoque}>"
