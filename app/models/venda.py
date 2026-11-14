"""Modelos ORM de venda e itens de venda."""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    Enum as SqlEnum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.produto import agora_utc

if TYPE_CHECKING:
    from app.models.produto import Produto


class StatusVenda(str, Enum):
    """Estados possíveis de uma venda."""

    CONCLUIDA = "CONCLUIDA"
    CANCELADA = "CANCELADA"


class Venda(Base):
    """Representa uma venda e o valor total calculado a partir dos itens."""

    __tablename__ = "vendas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    data_venda: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=agora_utc, index=True
    )
    total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    status: Mapped[StatusVenda] = mapped_column(
        SqlEnum(
            StatusVenda,
            name="status_venda",
            native_enum=False,
            validate_strings=True,
            length=20,
        ),
        nullable=False,
        default=StatusVenda.CONCLUIDA,
        index=True,
    )
    observacao: Mapped[str | None] = mapped_column(Text, nullable=True)
    cancelada_em: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    itens: Mapped[list["ItemVenda"]] = relationship(
        back_populates="venda",
        cascade="all, delete-orphan",
        order_by="ItemVenda.id",
    )

    def __repr__(self) -> str:  # pragma: no cover - helper de depuração
        return f"<Venda id={self.id} total={self.total} status={self.status.value}>"


class ItemVenda(Base):
    """Item de uma venda, com preço e nome do produto preservados como histórico."""

    __tablename__ = "itens_venda"
    __table_args__ = (
        UniqueConstraint("venda_id", "produto_id", name="uq_itens_venda_venda_produto"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    venda_id: Mapped[int] = mapped_column(
        ForeignKey("vendas.id", ondelete="CASCADE"), nullable=False, index=True
    )
    produto_id: Mapped[int] = mapped_column(
        ForeignKey("produtos.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    nome_produto: Mapped[str] = mapped_column(String(120), nullable=False)
    quantidade: Mapped[int] = mapped_column(Integer, nullable=False)
    preco_unitario: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    venda: Mapped["Venda"] = relationship(back_populates="itens")
    produto: Mapped["Produto"] = relationship(back_populates="itens_venda")

    def __repr__(self) -> str:  # pragma: no cover - helper de depuração
        return f"<ItemVenda venda_id={self.venda_id} produto_id={self.produto_id}>"
