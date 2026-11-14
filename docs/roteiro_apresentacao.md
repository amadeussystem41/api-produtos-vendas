# Roteiro de apresentação do projeto

Sugestão de demonstração com duração de 7 a 10 minutos, cobrindo todos os requisitos da atividade.

## Antes de começar (checklist)

- [ ] API rodando: `python -m uvicorn app.main:app --reload`
- [ ] Swagger aberto em `http://127.0.0.1:8000/docs`
- [ ] Postman aberto na coleção importada
- [ ] Terminal aberto na raiz do projeto, com a venv ativada
- [ ] Banco populado (opcional): `python -m app.seed`
- [ ] Git log disponível: `git log --oneline --decorate`
- [ ] GitHub aberto no repositório (se já publicado)
- [ ] Prints de evidência separados (pytest e Postman)

## Roteiro cronometrado

### 1. Abertura — 30 segundos

> "O projeto consiste em uma API REST para gestão de produtos e vendas. Ela foi desenvolvida em Python com FastAPI, usa SQLite com SQLAlchemy para persistência e possui documentação Swagger, testes automatizados e uma coleção Postman. O foco é controlar o estoque de forma segura: nenhuma venda pode deixar o estoque negativo."

Mostre a arquitetura do README e destaque a separação em **routers, services e models**.

### 2. Visão geral do Swagger — 45 segundos

1. Abra `/docs`.
2. Mostre os grupos **Sistema**, **Produtos** e **Vendas**.
3. Expanda `POST /api/v1/produtos` e comente os schemas e exemplos.
4. Mostre `GET /api/v1/vendas` e os filtros disponíveis.
5. Destaque que o Swagger é gerado automaticamente pelo FastAPI.

### 3. Cadastro e consulta de produtos — 1 minuto

1. Em `POST /api/v1/produtos`, clique em **Try it out** e envie:

   ```json
   {
     "nome": "Teclado Mecânico RGB",
     "descricao": "Teclado ABNT2 com switches azuis.",
     "categoria": "Periféricos",
     "sku": "DEMO-001",
     "preco": 249.90,
     "quantidade_estoque": 10
   }
   ```

2. Mostre o retorno **201** e copie o `id`.
3. Em `GET /api/v1/produtos`, use `busca=Teclado` e mostre o filtro e a paginação.
4. Em `GET /api/v1/produtos/{produto_id}`, consulte o produto e mostre `quantidade_estoque: 10`.
5. Em `PATCH /api/v1/produtos/{produto_id}`, altere o preço para `199.90` e confirme o retorno.

### 4. Registro de venda e baixa de estoque — 1 minuto

1. Em `POST /api/v1/vendas`, envie:

   ```json
   {
     "itens": [
       { "produto_id": 1, "quantidade": 3 }
     ],
     "observacao": "Demonstração em sala"
   }
   ```

2. Mostre o retorno **201**: status `CONCLUIDA`, total `599.70` e item com preço unitário.
3. Volte ao produto e mostre o estoque atualizado: **10 → 7**.
4. Explique que a operação é transacional: a venda e a baixa de estoque são confirmadas juntas.

### 5. Bloqueio de venda sem estoque — 45 segundos

1. Tente vender **999** unidades do mesmo produto.
2. Mostre o retorno **409 Conflict**:

   ```json
   {
     "detail": "Estoque insuficiente para 'Teclado Mecânico RGB' (SKU DEMO-001): disponível 7, solicitado 999."
   }
   ```

3. Consulte o produto novamente e mostre que o estoque continua **7**.
4. Destaque que nenhuma venda parcial foi registrada.

### 6. Histórico e cancelamento — 1 minuto

1. Em `GET /api/v1/vendas`, mostre a venda na listagem, ordenada da mais recente para a mais antiga.
2. Mostre os filtros `status=CONCLUIDA` e `data_inicio`.
3. Copie o `id` da venda e use `PATCH /api/v1/vendas/{venda_id}/cancelar`.
4. Mostre o status **CANCELADA**, a data de cancelamento e o estoque voltando para **10**.
5. Tente cancelar novamente e mostre o **409** (venda já cancelada).

### 7. Exclusão de produtos — 30 segundos

1. Crie um produto apenas para a demonstração.
2. `DELETE /api/v1/produtos/{id}` → **204**.
3. Consulte o produto → **404** (exclusão física, pois não possui vendas).
4. No produto que possui venda, o DELETE realiza **desativação lógica**; consulte e mostre `"ativo": false`.
5. Tente vender o produto inativo → **409**.

### 8. Testes automatizados — 45 segundos

No terminal, execute:

```powershell
python -m pytest -v
```

Mostre os **27 testes aprovados**. Destaque alguns cenários:

- estoque insuficiente;
- atomicidade com múltiplos itens;
- cancelamento com estorno;
- exclusão lógica;
- validação de payload.

### 9. Postman — 45 segundos

1. Abra a coleção **API de Gestão de Produtos e Vendas**.
2. Clique em **Run**.
3. Mostre as 4 pastas e explique que os IDs são salvos automaticamente em variáveis.
4. Execute e mostre os testes verdes, incluindo os 409 esperados.
5. Se preferir economizar tempo, mostre um print da execução já realizada.

### 10. Git/GitHub e encerramento — 45 segundos

1. Execute `git log --oneline --decorate --graph`.
2. Mostre os commits organizados por etapa.
3. Abra o GitHub e mostre README, estrutura e coleção Postman.
4. Encerre retomando os requisitos atendidos:

> "A API cobre cadastro, consulta, alteração e exclusão de produtos; registro e histórico de vendas; baixa e validação de estoque; Swagger; testes com Postman e pytest; e versionamento com Git/GitHub."

## Perguntas prováveis e respostas curtas

**Por que SQLite?**
É um banco relacional completo, não exige servidor e é ideal para o escopo acadêmico. A camada SQLAlchemy permite trocar para PostgreSQL alterando apenas `DATABASE_URL`.

**O que acontece se dois clientes comprarem o último item ao mesmo tempo?**
A venda usa transação e bloqueio de linha (`SELECT ... FOR UPDATE` no PostgreSQL). No SQLite as escritas são serializadas. A validação de estoque ocorre dentro da transação antes da baixa, e o commit é atômico.

**Por que o produto com vendas não é apagado de verdade?**
Para preservar a integridade e o histórico. A exclusão lógica mantém os dados da venda e impede novas vendas. Produtos sem vendas são removidos fisicamente.

**Por que o preço fica gravado no item da venda?**
Para que uma alteração futura no cadastro não modifique o valor histórico já vendido.

**Como o banco é criado?**
No `lifespan` do FastAPI, `Base.metadata.create_all` cria as tabelas. Em produção, o indicado seria usar migrações com Alembic.

**Onde estão as documentações?**
Swagger em `/docs`, ReDoc em `/redoc`, OpenAPI em `/openapi.json`, plano de testes em `docs/TESTES.md` e coleção em `docs/postman_collection.json`.

## Divisão de falas (se o grupo apresentar em equipe)

| Integrante | Parte sugerida |
|---|---|
| 1 | Abertura, arquitetura e tecnologias |
| 2 | Produtos e Swagger |
| 3 | Vendas, estoque e regras de negócio |
| 4 | Testes, Postman, Git e conclusão |

Ajuste a divisão conforme a quantidade de integrantes.
