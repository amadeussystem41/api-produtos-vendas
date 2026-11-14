"""Schemas de entrada e saída de produtos."""

from datetime import datetime
from decimal import Decimal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from app.schemas.comum import PaginacaoBase

_EXEMPLO_PRODUTO = {
    "nome": "Teclado Mecânico RGB",
    "descricao": "Teclado ABNT2 com switches azuis e iluminação RGB.",
    "categoria": "Periféricos",
    "sku": "TEC-RGB-001",
    "preco": 249.90,
    "quantidade_estoque": 25,
}


class ProdutoBase(BaseModel):
    """Campos comuns para criação e leitura de produtos."""

    model_config = ConfigDict(str_strip_whitespace=True)

    nome: str = Field(min_length=2, max_length=120, examples=["Teclado Mecânico RGB"])
    descricao: str | None = Field(
        default=None,
        max_length=1000,
        examples=["Teclado ABNT2 com switches azuis e iluminação RGB."],
    )
    categoria: str = Field(min_length=2, max_length=60, examples=["Periféricos"])
    sku: str = Field(
        min_length=3,
        max_length=50,
        pattern=r"^[A-Za-z0-9_-]+$",
        description="Código único de identificação do produto. Será salvo em maiúsculas.",
        examples=["TEC-RGB-001"],
    )
    preco: Decimal = Field(
        gt=0,
        max_digits=10,
        decimal_places=2,
        examples=[249.90],
    )
    quantidade_estoque: int = Field(ge=0, examples=[25])

    @field_validator("sku")
    @classmethod
    def normalizar_sku(cls, valor: str) -> str:
        """Padroniza o SKU em maiúsculas para evitar duplicidades."""
        return valor.strip().upper()


class ProdutoCriar(ProdutoBase):
    """Dados necessários para cadastrar um produto."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        json_schema_extra={"example": _EXEMPLO_PRODUTO},
    )


class ProdutoAtualizar(BaseModel):
    """Dados opcionais para atualização parcial de um produto."""

    model_config = ConfigDict(str_strip_whitespace=True)

    nome: str | None = Field(default=None, min_length=2, max_length=120)
    descricao: str | None = Field(default=None, max_length=1000)
    categoria: str | None = Field(default=None, min_length=2, max_length=60)
    sku: str | None = Field(
        default=None,
        min_length=3,
        max_length=50,
        pattern=r"^[A-Za-z0-9_-]+$",
    )
    preco: Decimal | None = Field(
        default=None, gt=0, max_digits=10, decimal_places=2
    )
    quantidade_estoque: int | None = Field(default=None, ge=0)
    ativo: bool | None = None

    _CAMPOS_OBRIGATORIOS = {
        "nome",
        "categoria",
        "sku",
        "preco",
        "quantidade_estoque",
        "ativo",
    }

    @field_validator("sku")
    @classmethod
    def normalizar_sku(cls, valor: str | None) -> str | None:
        """Padroniza o SKU em maiúsculas quando informado."""
        return valor.strip().upper() if valor is not None else None

    @model_validator(mode="after")
    def validar_campos_enviados(self) -> "ProdutoAtualizar":
        """Impede atualização vazia e valores nulos em campos obrigatórios."""
        if not self.model_fields_set:
            raise ValueError("Informe ao menos um campo para atualização.")

        for campo in self._CAMPOS_OBRIGATORIOS:
            if campo in self.model_fields_set and getattr(self, campo) is None:
                raise ValueError(f"O campo '{campo}' não pode ser nulo.")

        return self


class ProdutoResposta(ProdutoBase):
    """Representação completa de um produto retornado pela API."""

    model_config = ConfigDict(
        from_attributes=True,
        str_strip_whitespace=True,
        json_schema_extra={
            "example": {
                "id": 1,
                **_EXEMPLO_PRODUTO,
                "ativo": True,
                "criado_em": "2026-01-15T13:30:00",
                "atualizado_em": "2026-01-15T13:30:00",
            }
        },
    )

    id: int
    ativo: bool
    criado_em: datetime
    atualizado_em: datetime


class PaginaProdutos(PaginacaoBase):
    """Página de produtos com metadados de paginação."""

    itens: list[ProdutoResposta]
