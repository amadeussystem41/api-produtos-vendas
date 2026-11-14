"""Regras de negócio relacionadas a produtos."""

from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import ConflitoDeDadosError, RecursoNaoEncontradoError
from app.models import ItemVenda, Produto
from app.schemas.produto import ProdutoAtualizar, ProdutoCriar


def _validar_sku_unico(db: Session, sku: str, ignorar_id: int | None = None) -> None:
    """Garante que o SKU informado ainda não esteja em uso."""
    consulta = select(Produto.id).where(func.upper(Produto.sku) == sku.upper())
    if ignorar_id is not None:
        consulta = consulta.where(Produto.id != ignorar_id)

    if db.scalar(consulta) is not None:
        raise ConflitoDeDadosError(f"Já existe um produto cadastrado com o SKU '{sku}'.")


def criar_produto(db: Session, dados: ProdutoCriar) -> Produto:
    """Cadastra um novo produto."""
    _validar_sku_unico(db, dados.sku)

    produto = Produto(**dados.model_dump())
    db.add(produto)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ConflitoDeDadosError(
            f"Já existe um produto cadastrado com o SKU '{dados.sku}'."
        ) from None

    db.refresh(produto)
    return produto


def listar_produtos(
    db: Session,
    *,
    skip: int = 0,
    limit: int = 20,
    busca: str | None = None,
    categoria: str | None = None,
    ativo: bool | None = None,
) -> tuple[list[Produto], int]:
    """Lista produtos com filtros, busca textual e paginação."""
    consulta = select(Produto)
    filtros = []

    if busca:
        termo = f"%{busca.strip()}%"
        filtros.append(
            or_(
                Produto.nome.ilike(termo),
                Produto.sku.ilike(termo),
                Produto.descricao.ilike(termo),
            )
        )

    if categoria:
        filtros.append(func.lower(Produto.categoria) == categoria.strip().lower())

    if ativo is not None:
        filtros.append(Produto.ativo == ativo)

    if filtros:
        consulta = consulta.where(*filtros)

    total = db.scalar(select(func.count()).select_from(consulta.subquery())) or 0
    itens = db.scalars(
        consulta.order_by(Produto.nome.asc(), Produto.id.asc())
        .offset(skip)
        .limit(limit)
    ).all()

    return list(itens), total


def obter_produto(db: Session, produto_id: int) -> Produto:
    """Busca um produto pelo ID, incluindo produtos desativados."""
    produto = db.get(Produto, produto_id)
    if produto is None:
        raise RecursoNaoEncontradoError(
            f"Produto com id {produto_id} não encontrado."
        )
    return produto


def atualizar_produto(
    db: Session, produto_id: int, dados: ProdutoAtualizar
) -> Produto:
    """Atualiza parcialmente os dados de um produto."""
    produto = obter_produto(db, produto_id)
    alteracoes = dados.model_dump(exclude_unset=True)

    if "sku" in alteracoes:
        _validar_sku_unico(db, alteracoes["sku"], ignorar_id=produto.id)

    for campo, valor in alteracoes.items():
        setattr(produto, campo, valor)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ConflitoDeDadosError(
            "Não foi possível atualizar o produto: verifique se o SKU já está em uso."
        ) from None

    db.refresh(produto)
    return produto


def excluir_produto(db: Session, produto_id: int) -> None:
    """Exclui o produto ou o desativa quando ele possui histórico de vendas.

    A exclusão física é feita somente quando não existem vendas associadas,
    preservando a integridade do histórico. Produtos com vendas são
    desativados (exclusão lógica) e deixam de aceitar novas vendas.
    """
    produto = obter_produto(db, produto_id)

    possui_vendas = (
        db.scalar(
            select(func.count(ItemVenda.id)).where(
                ItemVenda.produto_id == produto_id
            )
        )
        or 0
    )

    if possui_vendas:
        produto.ativo = False
    else:
        db.delete(produto)

    db.commit()
