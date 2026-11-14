"""Script opcional para popular o banco com produtos de exemplo.

Uso:
    python -m app.seed
"""

from decimal import Decimal

from sqlalchemy import func, select

from app.database import SessionLocal, criar_tabelas
from app.models import Produto

PRODUTOS_EXEMPLO = [
    {
        "nome": "Teclado Mecânico RGB",
        "descricao": "Teclado ABNT2 com switches azuis e iluminação RGB.",
        "categoria": "Periféricos",
        "sku": "TEC-RGB-001",
        "preco": Decimal("249.90"),
        "quantidade_estoque": 25,
    },
    {
        "nome": "Mouse Gamer 16000 DPI",
        "descricao": "Mouse com sensor óptico de 16000 DPI e 7 botões.",
        "categoria": "Periféricos",
        "sku": "MOU-GAM-002",
        "preco": Decimal("189.90"),
        "quantidade_estoque": 40,
    },
    {
        "nome": 'Monitor 24" Full HD',
        "descricao": "Monitor LED de 24 polegadas, 75 Hz e entrada HDMI.",
        "categoria": "Monitores",
        "sku": "MON-FHD-003",
        "preco": Decimal("899.00"),
        "quantidade_estoque": 12,
    },
    {
        "nome": "Headset com Microfone",
        "descricao": "Headset over-ear com som estéreo e microfone removível.",
        "categoria": "Áudio",
        "sku": "HEA-MIC-004",
        "preco": Decimal("159.90"),
        "quantidade_estoque": 30,
    },
    {
        "nome": "Cadeira Gamer Ergonômica",
        "descricao": "Cadeira com apoio de braço ajustável e encosto reclinável.",
        "categoria": "Móveis",
        "sku": "CAD-ERG-005",
        "preco": Decimal("1299.00"),
        "quantidade_estoque": 8,
    },
]


def executar_seed() -> None:
    """Insere os produtos de exemplo que ainda não existem no banco."""
    criar_tabelas()

    with SessionLocal() as db:
        criados = 0
        for dados in PRODUTOS_EXEMPLO:
            existente = db.scalar(
                select(Produto).where(Produto.sku == dados["sku"])
            )
            if existente is None:
                db.add(Produto(**dados))
                criados += 1
        db.commit()

        total = db.scalar(select(func.count()).select_from(Produto)) or 0

    print(f"Seed concluido. Produtos criados agora: {criados}. Total no banco: {total}.")


if __name__ == "__main__":
    executar_seed()
