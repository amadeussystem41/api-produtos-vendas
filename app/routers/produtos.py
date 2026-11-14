"""Rotas de cadastro e manutenção de produtos."""

from typing import Annotated

from fastapi import APIRouter, Path, Query, Response, status

from app.dependencies import DbSession
from app.schemas.comum import ErroResposta
from app.schemas.produto import (
    PaginaProdutos,
    ProdutoAtualizar,
    ProdutoCriar,
    ProdutoResposta,
)
from app.services import produto_service

router = APIRouter(prefix="/produtos", tags=["Produtos"])

_RESPOSTAS_PRODUTO = {
    404: {"model": ErroResposta, "description": "Produto não encontrado."},
    409: {"model": ErroResposta, "description": "SKU já cadastrado."},
}


@router.post(
    "",
    response_model=ProdutoResposta,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastrar produto",
    description=(
        "Cadastra um produto com SKU único. O SKU é normalizado para letras "
        "maiúsculas e a quantidade inicial em estoque deve ser maior ou igual a zero."
    ),
    responses={409: _RESPOSTAS_PRODUTO[409], 422: {"description": "Dados inválidos."}},
)
def criar_produto(payload: ProdutoCriar, db: DbSession) -> ProdutoResposta:
    """Cria um novo produto no catálogo."""
    return produto_service.criar_produto(db, payload)


@router.get(
    "",
    response_model=PaginaProdutos,
    summary="Listar e consultar produtos",
    description=(
        "Retorna uma lista paginada de produtos. É possível buscar por nome, SKU "
        "ou descrição, filtrar por categoria e pela situação (ativo/inativo)."
    ),
)
def listar_produtos(
    db: DbSession,
    skip: Annotated[int, Query(ge=0, description="Registros a ignorar.")] = 0,
    limit: Annotated[
        int, Query(ge=1, le=100, description="Tamanho máximo da página.")
    ] = 20,
    busca: Annotated[
        str | None,
        Query(
            min_length=1,
            max_length=120,
            description="Termo buscado em nome, SKU ou descrição.",
        ),
    ] = None,
    categoria: Annotated[
        str | None, Query(min_length=2, max_length=60, description="Categoria exata.")
    ] = None,
    ativo: Annotated[
        bool | None,
        Query(description="Filtra por produtos ativos (true) ou inativos (false)."),
    ] = None,
) -> PaginaProdutos:
    """Lista produtos com filtros e paginação."""
    itens, total = produto_service.listar_produtos(
        db,
        skip=skip,
        limit=limit,
        busca=busca,
        categoria=categoria,
        ativo=ativo,
    )
    return PaginaProdutos(itens=itens, total=total, skip=skip, limit=limit)


@router.get(
    "/{produto_id}",
    response_model=ProdutoResposta,
    summary="Consultar produto por ID",
    description="Retorna os dados de um produto, inclusive se estiver inativo.",
    responses={404: _RESPOSTAS_PRODUTO[404]},
)
def obter_produto(
    db: DbSession,
    produto_id: Annotated[int, Path(ge=1, description="ID do produto.")],
) -> ProdutoResposta:
    """Consulta um produto específico."""
    return produto_service.obter_produto(db, produto_id)


@router.patch(
    "/{produto_id}",
    response_model=ProdutoResposta,
    summary="Atualizar produto",
    description=(
        "Atualiza apenas os campos enviados no corpo da requisição. Também pode "
        "ser usado para reativar um produto com `ativo: true`."
    ),
    responses=_RESPOSTAS_PRODUTO,
)
def atualizar_produto(
    payload: ProdutoAtualizar,
    db: DbSession,
    produto_id: Annotated[int, Path(ge=1, description="ID do produto.")],
) -> ProdutoResposta:
    """Atualiza parcialmente os dados de um produto."""
    return produto_service.atualizar_produto(db, produto_id, payload)


@router.delete(
    "/{produto_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    summary="Excluir produto",
    description=(
        "Exclui o produto quando ele nunca foi vendido. Caso existam vendas "
        "associadas, o produto é desativado (exclusão lógica) para preservar o "
        "histórico, deixando de aparecer como disponível para novas vendas."
    ),
    responses={404: _RESPOSTAS_PRODUTO[404]},
)
def excluir_produto(
    db: DbSession,
    produto_id: Annotated[int, Path(ge=1, description="ID do produto.")],
) -> None:
    """Remove ou desativa um produto."""
    produto_service.excluir_produto(db, produto_id)
