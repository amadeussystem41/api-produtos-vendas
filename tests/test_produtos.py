"""Testes das funcionalidades de produtos."""

from decimal import Decimal

import pytest
from fastapi.testclient import TestClient


def test_health_check_e_swagger_disponiveis(app_client: TestClient) -> None:
    resposta = app_client.get("/health")
    assert resposta.status_code == 200
    assert resposta.json()["status"] == "ok"
    assert resposta.json()["banco_de_dados"] == "conectado"

    documentacao = app_client.get("/docs")
    assert documentacao.status_code == 200

    openapi = app_client.get("/openapi.json")
    assert openapi.status_code == 200
    caminhos = openapi.json()["paths"]
    assert "/api/v1/produtos" in caminhos
    assert "/api/v1/vendas" in caminhos


def test_cadastrar_produto_normaliza_sku(
    app_client: TestClient, criar_produto
) -> None:
    produto = criar_produto(
        nome="  Teclado Mecânico  ",
        sku="tec-rgb-001",
        preco="249.90",
        quantidade_estoque=25,
    )

    assert produto["id"] > 0
    assert produto["nome"] == "Teclado Mecânico"
    assert produto["sku"] == "TEC-RGB-001"
    assert Decimal(str(produto["preco"])) == Decimal("249.90")
    assert produto["quantidade_estoque"] == 25
    assert produto["ativo"] is True
    assert produto["criado_em"]
    assert produto["atualizado_em"]


def test_nao_permite_sku_duplicado(
    app_client: TestClient, criar_produto
) -> None:
    criar_produto(sku="SKU-UNICO")

    resposta = app_client.post(
        "/api/v1/produtos",
        json={
            "nome": "Outro produto",
            "categoria": "Testes",
            "sku": "sku-unico",
            "preco": "10.00",
            "quantidade_estoque": 1,
        },
    )

    assert resposta.status_code == 409
    assert "SKU" in resposta.json()["detail"]


@pytest.mark.parametrize(
    "campo, valor",
    [
        ("preco", "0"),
        ("preco", "-5.00"),
        ("quantidade_estoque", -1),
        ("nome", "A"),
        ("sku", "com espaço"),
    ],
)
def test_validacao_de_dados_do_produto(
    app_client: TestClient, campo: str, valor
) -> None:
    payload = {
        "nome": "Produto Válido",
        "categoria": "Testes",
        "sku": "VALIDO-001",
        "preco": "10.00",
        "quantidade_estoque": 5,
    }
    payload[campo] = valor

    resposta = app_client.post("/api/v1/produtos", json=payload)

    assert resposta.status_code == 422


def test_listar_com_busca_categoria_e_paginacao(
    app_client: TestClient, criar_produto
) -> None:
    criar_produto(nome="Teclado Mecânico", categoria="Periféricos", sku="TEC-001")
    criar_produto(nome="Mouse Gamer", categoria="Periféricos", sku="MOU-001")
    criar_produto(nome="Monitor 24 polegadas", categoria="Monitores", sku="MON-001")

    busca = app_client.get("/api/v1/produtos", params={"busca": "teclado"})
    assert busca.status_code == 200
    assert busca.json()["total"] == 1
    assert busca.json()["itens"][0]["nome"] == "Teclado Mecânico"

    categoria = app_client.get(
        "/api/v1/produtos", params={"categoria": "periféricos"}
    )
    assert categoria.status_code == 200
    assert categoria.json()["total"] == 2

    pagina = app_client.get(
        "/api/v1/produtos", params={"skip": 0, "limit": 2}
    )
    assert pagina.status_code == 200
    assert pagina.json()["total"] == 3
    assert len(pagina.json()["itens"]) == 2
    assert pagina.json()["limit"] == 2


def test_consultar_produto_por_id(app_client: TestClient, criar_produto) -> None:
    produto = criar_produto()

    resposta = app_client.get(f"/api/v1/produtos/{produto['id']}")
    assert resposta.status_code == 200
    assert resposta.json()["id"] == produto["id"]

    inexistente = app_client.get("/api/v1/produtos/9999")
    assert inexistente.status_code == 404
    assert "não encontrado" in inexistente.json()["detail"]


def test_atualizar_produto_parcialmente(
    app_client: TestClient, criar_produto
) -> None:
    produto = criar_produto(preco="100.00", quantidade_estoque=3)

    resposta = app_client.patch(
        f"/api/v1/produtos/{produto['id']}",
        json={"preco": "89.90", "quantidade_estoque": 15},
    )

    assert resposta.status_code == 200
    atualizado = resposta.json()
    assert Decimal(str(atualizado["preco"])) == Decimal("89.90")
    assert atualizado["quantidade_estoque"] == 15
    assert atualizado["nome"] == produto["nome"]


def test_atualizacao_deve_ter_ao_menos_um_campo(
    app_client: TestClient, criar_produto
) -> None:
    produto = criar_produto()

    resposta = app_client.patch(
        f"/api/v1/produtos/{produto['id']}", json={}
    )
    assert resposta.status_code == 422

    resposta_nula = app_client.patch(
        f"/api/v1/produtos/{produto['id']}", json={"preco": None}
    )
    assert resposta_nula.status_code == 422


def test_atualizar_sku_duplicado_retorna_conflito(
    app_client: TestClient, criar_produto
) -> None:
    primeiro = criar_produto(sku="SKU-A")
    criar_produto(sku="SKU-B")

    resposta = app_client.patch(
        f"/api/v1/produtos/{primeiro['id']}", json={"sku": "SKU-B"}
    )

    assert resposta.status_code == 409


def test_excluir_produto_sem_vendas_remove_registro(
    app_client: TestClient, criar_produto
) -> None:
    produto = criar_produto()

    resposta = app_client.delete(f"/api/v1/produtos/{produto['id']}")
    assert resposta.status_code == 204
    assert resposta.content == b""

    consulta = app_client.get(f"/api/v1/produtos/{produto['id']}")
    assert consulta.status_code == 404

    listagem = app_client.get("/api/v1/produtos")
    assert listagem.json()["total"] == 0


def test_excluir_produto_com_vendas_desativa(
    app_client: TestClient, criar_produto
) -> None:
    produto = criar_produto(quantidade_estoque=5)

    venda = app_client.post(
        "/api/v1/vendas",
        json={"itens": [{"produto_id": produto["id"], "quantidade": 1}]},
    )
    assert venda.status_code == 201

    resposta = app_client.delete(f"/api/v1/produtos/{produto['id']}")
    assert resposta.status_code == 204

    consulta = app_client.get(f"/api/v1/produtos/{produto['id']}")
    assert consulta.status_code == 200
    assert consulta.json()["ativo"] is False

    nova_venda = app_client.post(
        "/api/v1/vendas",
        json={"itens": [{"produto_id": produto["id"], "quantidade": 1}]},
    )
    assert nova_venda.status_code == 409
    assert "inativo" in nova_venda.json()["detail"]


def test_reativar_produto_desativado(
    app_client: TestClient, criar_produto
) -> None:
    produto = criar_produto(quantidade_estoque=2)
    app_client.post(
        "/api/v1/vendas",
        json={"itens": [{"produto_id": produto["id"], "quantidade": 1}]},
    )
    app_client.delete(f"/api/v1/produtos/{produto['id']}")

    resposta = app_client.patch(
        f"/api/v1/produtos/{produto['id']}", json={"ativo": True}
    )

    assert resposta.status_code == 200
    assert resposta.json()["ativo"] is True
