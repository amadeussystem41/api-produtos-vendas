"""Rotas de registro, consulta e cancelamento de vendas."""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Path, Query, status

from app.dependencies import DbSession
from app.models.venda import StatusVenda
from app.schemas.comum import ErroResposta
from app.schemas.venda import PaginaVendas, VendaCriar, VendaResposta
from app.services import venda_service

router = APIRouter(prefix="/vendas", tags=["Vendas"])


@router.post(
    "",
    response_model=VendaResposta,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar venda",
    description=(
        "Registra uma venda, calcula o total, grava o preço de cada item e "
        "atualiza o estoque. A operação é transacional: se qualquer produto não "
        "existir, estiver inativo ou tiver estoque insuficiente, nada é alterado. "
        "Itens repetidos do mesmo produto são agrupados automaticamente."
    ),
    responses={
        404: {"model": ErroResposta, "description": "Produto não encontrado."},
        409: {
            "model": ErroResposta,
            "description": "Estoque insuficiente ou produto inativo.",
        },
        422: {"description": "Dados inválidos."},
    },
)
def registrar_venda(payload: VendaCriar, db: DbSession) -> VendaResposta:
    """Registra uma nova venda e baixa o estoque."""
    return venda_service.registrar_venda(db, payload)


@router.get(
    "",
    response_model=PaginaVendas,
    summary="Consultar histórico de vendas",
    description=(
        "Retorna o histórico paginado de vendas com seus itens. Permite filtrar "
        "por status e por intervalo de datas (UTC)."
    ),
)
def listar_vendas(
    db: DbSession,
    skip: Annotated[int, Query(ge=0, description="Registros a ignorar.")] = 0,
    limit: Annotated[
        int, Query(ge=1, le=100, description="Tamanho máximo da página.")
    ] = 20,
    status_venda: Annotated[
        StatusVenda | None,
        Query(alias="status", description="Status da venda."),
    ] = None,
    data_inicio: Annotated[
        datetime | None,
        Query(description="Data/hora inicial do período (ISO 8601)."),
    ] = None,
    data_fim: Annotated[
        datetime | None,
        Query(description="Data/hora final do período (ISO 8601)."),
    ] = None,
) -> PaginaVendas:
    """Consulta vendas com filtros e paginação."""
    itens, total = venda_service.listar_vendas(
        db,
        skip=skip,
        limit=limit,
        status=status_venda,
        data_inicio=data_inicio,
        data_fim=data_fim,
    )
    return PaginaVendas(itens=itens, total=total, skip=skip, limit=limit)


@router.get(
    "/{venda_id}",
    response_model=VendaResposta,
    summary="Consultar venda por ID",
    description="Retorna os dados completos de uma venda e seus itens.",
    responses={404: {"model": ErroResposta, "description": "Venda não encontrada."}},
)
def obter_venda(
    db: DbSession,
    venda_id: Annotated[int, Path(ge=1, description="ID da venda.")],
) -> VendaResposta:
    """Consulta uma venda específica."""
    return venda_service.obter_venda(db, venda_id)


@router.patch(
    "/{venda_id}/cancelar",
    response_model=VendaResposta,
    summary="Cancelar venda",
    description=(
        "Cancela uma venda concluída e devolve todos os itens ao estoque. "
        "Uma venda já cancelada não pode ser cancelada novamente."
    ),
    responses={
        404: {"model": ErroResposta, "description": "Venda não encontrada."},
        409: {"model": ErroResposta, "description": "Venda já cancelada."},
    },
)
def cancelar_venda(
    db: DbSession,
    venda_id: Annotated[int, Path(ge=1, description="ID da venda.")],
) -> VendaResposta:
    """Cancela a venda e estorna o estoque."""
    return venda_service.cancelar_venda(db, venda_id)
