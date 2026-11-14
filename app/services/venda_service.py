"""Regras de negócio relacionadas a vendas e controle de estoque."""

from datetime import datetime, timezone
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import (
    ConflitoDeDadosError,
    EstoqueInsuficienteError,
    RecursoNaoEncontradoError,
)
from app.models import ItemVenda, Produto, StatusVenda, Venda
from app.models.produto import agora_utc
from app.schemas.venda import VendaCriar

CENTAVOS = Decimal("0.01")


def _utc_naive(valor: datetime) -> datetime:
    """Normaliza uma data recebida para UTC sem timezone."""
    if valor.tzinfo is None:
        return valor
    return valor.astimezone(timezone.utc).replace(tzinfo=None)


def _agregar_itens(dados: VendaCriar) -> dict[int, int]:
    """Agrupa itens repetidos para validar e deduzir o estoque uma única vez."""
    quantidades: dict[int, int] = {}
    for item in dados.itens:
        quantidades[item.produto_id] = (
            quantidades.get(item.produto_id, 0) + item.quantidade
        )
    return quantidades


def registrar_venda(db: Session, dados: VendaCriar) -> Venda:
    """Registra a venda de forma transacional e atualiza o estoque.

    Todas as validações de existência, disponibilidade e estoque acontecem
    antes de qualquer alteração. Se algum item falhar, nenhum produto é
    debitado (operação atômica).
    """
    quantidades = _agregar_itens(dados)

    produtos = db.scalars(
        select(Produto)
        .where(Produto.id.in_(quantidades.keys()))
        .with_for_update()
    ).all()
    produtos_por_id = {produto.id: produto for produto in produtos}

    ids_inexistentes = [
        produto_id for produto_id in quantidades if produto_id not in produtos_por_id
    ]
    if ids_inexistentes:
        db.rollback()
        ids = ", ".join(str(produto_id) for produto_id in ids_inexistentes)
        raise RecursoNaoEncontradoError(
            f"Produto(s) não encontrado(s) para o(s) id(s): {ids}."
        )

    for produto_id, quantidade in quantidades.items():
        produto = produtos_por_id[produto_id]

        if not produto.ativo:
            db.rollback()
            raise ConflitoDeDadosError(
                f"O produto '{produto.nome}' (SKU {produto.sku}) está inativo "
                "e não pode ser vendido."
            )

        if produto.quantidade_estoque < quantidade:
            db.rollback()
            raise EstoqueInsuficienteError(
                f"Estoque insuficiente para '{produto.nome}' (SKU {produto.sku}): "
                f"disponível {produto.quantidade_estoque}, solicitado {quantidade}."
            )

    venda = Venda(
        status=StatusVenda.CONCLUIDA,
        observacao=dados.observacao,
        total=Decimal("0.00"),
    )
    db.add(venda)
    db.flush()

    total = Decimal("0.00")
    for produto_id, quantidade in quantidades.items():
        produto = produtos_por_id[produto_id]
        preco_unitario = Decimal(produto.preco)
        subtotal = (preco_unitario * quantidade).quantize(
            CENTAVOS, rounding=ROUND_HALF_UP
        )

        db.add(
            ItemVenda(
                venda_id=venda.id,
                produto_id=produto.id,
                nome_produto=produto.nome,
                quantidade=quantidade,
                preco_unitario=preco_unitario,
                subtotal=subtotal,
            )
        )
        produto.quantidade_estoque -= quantidade
        total += subtotal

    venda.total = total.quantize(CENTAVOS, rounding=ROUND_HALF_UP)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ConflitoDeDadosError(
            "Não foi possível registrar a venda. Tente novamente."
        ) from None

    return obter_venda(db, venda.id)


def listar_vendas(
    db: Session,
    *,
    skip: int = 0,
    limit: int = 20,
    status: StatusVenda | None = None,
    data_inicio: datetime | None = None,
    data_fim: datetime | None = None,
) -> tuple[list[Venda], int]:
    """Consulta o histórico de vendas com filtros e paginação."""
    consulta = select(Venda).options(selectinload(Venda.itens))

    if status is not None:
        consulta = consulta.where(Venda.status == status)

    if data_inicio is not None:
        consulta = consulta.where(Venda.data_venda >= _utc_naive(data_inicio))

    if data_fim is not None:
        consulta = consulta.where(Venda.data_venda <= _utc_naive(data_fim))

    total = db.scalar(select(func.count()).select_from(consulta.subquery())) or 0
    itens = db.scalars(
        consulta.order_by(Venda.data_venda.desc(), Venda.id.desc())
        .offset(skip)
        .limit(limit)
    ).all()

    return list(itens), total


def obter_venda(db: Session, venda_id: int) -> Venda:
    """Busca uma venda pelo ID, carregando seus itens."""
    venda = db.scalar(
        select(Venda)
        .options(selectinload(Venda.itens))
        .where(Venda.id == venda_id)
    )
    if venda is None:
        raise RecursoNaoEncontradoError(f"Venda com id {venda_id} não encontrada.")
    return venda


def cancelar_venda(db: Session, venda_id: int) -> Venda:
    """Cancela uma venda e devolve os itens ao estoque."""
    venda = obter_venda(db, venda_id)

    if venda.status is StatusVenda.CANCELADA:
        raise ConflitoDeDadosError(f"A venda com id {venda_id} já está cancelada.")

    for item in venda.itens:
        produto = db.get(Produto, item.produto_id)
        if produto is not None:
            produto.quantidade_estoque += item.quantidade

    venda.status = StatusVenda.CANCELADA
    venda.cancelada_em = agora_utc()

    db.commit()
    return obter_venda(db, venda_id)
