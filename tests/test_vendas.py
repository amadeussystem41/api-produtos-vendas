"""Testes das funcionalidades de vendas e controle de estoque."""

from decimal import Decimal

from fastapi.testclient import TestClient


def _criar_venda(client: TestClient, itens: list[dict], **extras):
    payload = {"itens": itens, **extras}
    return client.post("/api/v1/vendas", json=payload)


def _estoque(client: TestClient, produto_id: int) -> int:
    resposta = client.get(f"/api/v1/produtos/{produto_id}")
    assert resposta.status_code == 200
    return resposta.json()["quantidade_estoque"]


def test_registrar_venda_e_baixar_estoque(
    app_client: TestClient, criar_produto
) -> None:
    produto = criar_produto(preco="100.00", quantidade_estoque=10)

    resposta = _criar_venda(
        app_client,
        [{"produto_id": produto["id"], "quantidade": 3}],
        observacao="Venda de teste",
    )

    assert resposta.status_code == 201
    venda = resposta.json()
    assert venda["id"] > 0
    assert venda["status"] == "CONCLUIDA"
    assert venda["observacao"] == "Venda de teste"
    assert venda["cancelada_em"] is None
    assert Decimal(str(venda["total"])) == Decimal("300.00")

    assert len(venda["itens"]) == 1
    item = venda["itens"][0]
    assert item["produto_id"] == produto["id"]
    assert item["nome_produto"] == produto["nome"]
    assert item["quantidade"] == 3
    assert Decimal(str(item["preco_unitario"])) == Decimal("100.00")
    assert Decimal(str(item["subtotal"])) == Decimal("300.00")

    assert _estoque(app_client, produto["id"]) == 7


def test_venda_com_multiplos_produtos_calcula_total(
    app_client: TestClient, criar_produto
) -> None:
    teclado = criar_produto(preco="50.00", quantidade_estoque=5)
    mouse = criar_produto(preco="30.50", quantidade_estoque=5)

    resposta = _criar_venda(
        app_client,
        [
            {"produto_id": teclado["id"], "quantidade": 2},
            {"produto_id": mouse["id"], "quantidade": 3},
        ],
    )

    assert resposta.status_code == 201
    venda = resposta.json()
    assert Decimal(str(venda["total"])) == Decimal("191.50")
    assert len(venda["itens"]) == 2
    assert _estoque(app_client, teclado["id"]) == 3
    assert _estoque(app_client, mouse["id"]) == 2


def test_itens_repetidos_sao_agrupados(
    app_client: TestClient, criar_produto
) -> None:
    produto = criar_produto(quantidade_estoque=5)

    resposta = _criar_venda(
        app_client,
        [
            {"produto_id": produto["id"], "quantidade": 2},
            {"produto_id": produto["id"], "quantidade": 3},
        ],
    )

    assert resposta.status_code == 201
    venda = resposta.json()
    assert len(venda["itens"]) == 1
    assert venda["itens"][0]["quantidade"] == 5
    assert _estoque(app_client, produto["id"]) == 0


def test_venda_sem_estoque_suficiente_e_bloqueada(
    app_client: TestClient, criar_produto
) -> None:
    produto = criar_produto(quantidade_estoque=2)

    resposta = _criar_venda(
        app_client,
        [{"produto_id": produto["id"], "quantidade": 3}],
    )

    assert resposta.status_code == 409
    detalhe = resposta.json()["detail"]
    assert "Estoque insuficiente" in detalhe
    assert "disponível 2" in detalhe
    assert "solicitado 3" in detalhe

    assert _estoque(app_client, produto["id"]) == 2
    historico = app_client.get("/api/v1/vendas")
    assert historico.json()["total"] == 0


def test_venda_e_transacional_quando_um_item_falha(
    app_client: TestClient, criar_produto
) -> None:
    produto_ok = criar_produto(quantidade_estoque=10)
    produto_sem_estoque = criar_produto(quantidade_estoque=1)

    resposta = _criar_venda(
        app_client,
        [
            {"produto_id": produto_ok["id"], "quantidade": 2},
            {"produto_id": produto_sem_estoque["id"], "quantidade": 5},
        ],
    )

    assert resposta.status_code == 409
    # Mesmo o primeiro item sendo válido, nada foi debitado.
    assert _estoque(app_client, produto_ok["id"]) == 10
    assert _estoque(app_client, produto_sem_estoque["id"]) == 1
    assert app_client.get("/api/v1/vendas").json()["total"] == 0


def test_venda_com_produto_inexistente(
    app_client: TestClient, criar_produto
) -> None:
    criar_produto()

    resposta = _criar_venda(
        app_client,
        [{"produto_id": 99999, "quantidade": 1}],
    )

    assert resposta.status_code == 404
    assert "não encontrado" in resposta.json()["detail"]


def test_venda_de_produto_inativo_e_bloqueada(
    app_client: TestClient, criar_produto
) -> None:
    produto = criar_produto(quantidade_estoque=5)
    app_client.patch(
        f"/api/v1/produtos/{produto['id']}", json={"ativo": False}
    )

    resposta = _criar_venda(
        app_client,
        [{"produto_id": produto["id"], "quantidade": 1}],
    )

    assert resposta.status_code == 409
    assert "inativo" in resposta.json()["detail"]


def test_consultar_historico_e_detalhe(
    app_client: TestClient, criar_produto
) -> None:
    produto = criar_produto(preco="25.00", quantidade_estoque=10)

    primeira = _criar_venda(
        app_client, [{"produto_id": produto["id"], "quantidade": 1}]
    )
    segunda = _criar_venda(
        app_client, [{"produto_id": produto["id"], "quantidade": 2}]
    )
    assert primeira.status_code == segunda.status_code == 201

    historico = app_client.get("/api/v1/vendas", params={"limit": 10})
    assert historico.status_code == 200
    corpo = historico.json()
    assert corpo["total"] == 2
    assert [item["id"] for item in corpo["itens"]] == [
        segunda.json()["id"],
        primeira.json()["id"],
    ]

    detalhe = app_client.get(f"/api/v1/vendas/{primeira.json()['id']}")
    assert detalhe.status_code == 200
    assert detalhe.json()["itens"][0]["quantidade"] == 1

    inexistente = app_client.get("/api/v1/vendas/9999")
    assert inexistente.status_code == 404

    periodo_passado = app_client.get(
        "/api/v1/vendas",
        params={
            "data_inicio": "2000-01-01T00:00:00",
            "data_fim": "2000-01-02T00:00:00",
        },
    )
    assert periodo_passado.status_code == 200
    assert periodo_passado.json()["total"] == 0


def test_cancelar_venda_estorna_estoque(
    app_client: TestClient, criar_produto
) -> None:
    produto = criar_produto(preco="40.00", quantidade_estoque=10)
    venda = _criar_venda(
        app_client, [{"produto_id": produto["id"], "quantidade": 4}]
    ).json()
    assert _estoque(app_client, produto["id"]) == 6

    resposta = app_client.patch(f"/api/v1/vendas/{venda['id']}/cancelar")

    assert resposta.status_code == 200
    cancelada = resposta.json()
    assert cancelada["status"] == "CANCELADA"
    assert cancelada["cancelada_em"] is not None
    assert cancelada["total"] == venda["total"]
    assert _estoque(app_client, produto["id"]) == 10

    repetida = app_client.patch(f"/api/v1/vendas/{venda['id']}/cancelar")
    assert repetida.status_code == 409
    assert "já está cancelada" in repetida.json()["detail"]

    canceladas = app_client.get(
        "/api/v1/vendas", params={"status": "CANCELADA"}
    )
    assert canceladas.json()["total"] == 1

    concluidas = app_client.get(
        "/api/v1/vendas", params={"status": "CONCLUIDA"}
    )
    assert concluidas.json()["total"] == 0


def test_venda_preserva_preco_do_momento_da_compra(
    app_client: TestClient, criar_produto
) -> None:
    produto = criar_produto(preco="100.00", quantidade_estoque=5)
    venda = _criar_venda(
        app_client, [{"produto_id": produto["id"], "quantidade": 2}]
    ).json()

    app_client.patch(
        f"/api/v1/produtos/{produto['id']}", json={"preco": "150.00"}
    )

    consulta = app_client.get(f"/api/v1/vendas/{venda['id']}")
    item = consulta.json()["itens"][0]
    assert Decimal(str(item["preco_unitario"])) == Decimal("100.00")
    assert Decimal(str(item["subtotal"])) == Decimal("200.00")


def test_validacao_do_payload_de_venda(
    app_client: TestClient, criar_produto
) -> None:
    produto = criar_produto()

    sem_itens = _criar_venda(app_client, [])
    assert sem_itens.status_code == 422

    quantidade_zero = _criar_venda(
        app_client, [{"produto_id": produto["id"], "quantidade": 0}]
    )
    assert quantidade_zero.status_code == 422

    sem_produto_id = _criar_venda(
        app_client, [{"produto_id": None, "quantidade": 1}]
    )
    assert sem_produto_id.status_code == 422
