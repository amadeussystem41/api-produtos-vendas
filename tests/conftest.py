"""Fixtures compartilhadas pelos testes automatizados."""

from collections.abc import Generator
from itertools import count

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app


@pytest.fixture()
def app_client() -> Generator[TestClient, None, None]:
    """Cria um cliente HTTP usando um banco SQLite isolado em memória."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session = sessionmaker(
        bind=engine, autoflush=False, expire_on_commit=False
    )
    Base.metadata.create_all(bind=engine)

    def override_get_db() -> Generator:
        db = testing_session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture()
def criar_produto(app_client: TestClient):
    """Fábrica de produtos para reduzir a repetição nos testes."""
    sequencia = count(1)

    def _criar(**alteracoes) -> dict:
        numero = next(sequencia)
        payload = {
            "nome": f"Produto de Teste {numero}",
            "descricao": "Produto criado automaticamente pelos testes.",
            "categoria": "Testes",
            "sku": f"TESTE-{numero:03d}",
            "preco": "100.00",
            "quantidade_estoque": 10,
        }
        payload.update(alteracoes)

        resposta = app_client.post("/api/v1/produtos", json=payload)
        assert resposta.status_code == 201, resposta.text
        return resposta.json()

    return _criar
