# Plano e evidências de testes

Este documento descreve os testes executados para validar a API, tanto de forma automatizada quanto manual.

## 1. Resumo

| Tipo | Ferramenta | Quantidade | Resultado |
|---|---|---|---|
| Automatizados | pytest + FastAPI TestClient | 27 testes | Aprovados |
| Manuais / integração | Postman (Collection Runner) | 23 requisições | Aprovadas |
| Documentação | Swagger / OpenAPI | 7 caminhos, 11 operações | Disponíveis |

Ambiente utilizado:

- Windows 11
- Python 3.12.10
- FastAPI 0.163.0
- SQLAlchemy 2.1.8
- SQLite
- pytest 8.4.2
- Postman

## 2. Testes automatizados

### Como executar

```powershell
# Na raiz do projeto, com a venv ativada
python -m pytest -v
```

Saída esperada:

```text
============================= test session starts =============================
collected 27 items

tests/test_produtos.py ................                             [ 59%]
tests/test_vendas.py ...........                                     [100%]

============================= 27 passed =============================
```

> O pytest cria um banco SQLite em memória para cada teste e o descarta ao final, garantindo isolamento e repetibilidade.

### Casos automatizados

#### Produtos — `tests/test_produtos.py`

| # | Cenário | Resultado esperado |
|---|---|---|
| 1 | Health check e Swagger/OpenAPI disponíveis | 200; rotas presentes no OpenAPI |
| 2 | Cadastrar produto com SKU minúsculo e nome com espaços | 201; SKU em maiúsculas e nome normalizado |
| 3 | Cadastrar produto com SKU já existente (maiúsculas/minúsculas) | 409 |
| 4–8 | Preço zero, preço negativo, estoque negativo, nome curto e SKU inválido | 422 |
| 9 | Listar com busca, categoria (case-insensitive) e paginação | 200; total e itens corretos |
| 10 | Consultar por ID existente e inexistente | 200 e 404 |
| 11 | Atualizar preço e estoque parcialmente | 200; demais campos preservados |
| 12 | Atualizar sem campos ou com campo obrigatório nulo | 422 |
| 13 | Atualizar para SKU já usado por outro produto | 409 |
| 14 | Excluir produto sem vendas | 204; consulta posterior retorna 404 |
| 15 | Excluir produto com venda | 204; produto fica inativo; nova venda retorna 409 |
| 16 | Reativar produto via PATCH `ativo: true` | 200; produto ativo |

#### Vendas e estoque — `tests/test_vendas.py`

| # | Cenário | Resultado esperado |
|---|---|---|
| 17 | Registrar venda de 3 unidades | 201; total 300,00; estoque 10 → 7 |
| 18 | Venda com dois produtos e preços diferentes | 201; total 191,50; estoques atualizados |
| 19 | Itens repetidos do mesmo produto | 201; itens agrupados; baixa única |
| 20 | Venda com quantidade maior que o estoque | 409; estoque inalterado; nenhuma venda criada |
| 21 | Venda de dois produtos em que o segundo não tem estoque | 409; nenhum dos dois estoques é debitado |
| 22 | Venda com produto inexistente | 404 |
| 23 | Venda com produto inativo | 409 |
| 24 | Histórico, ordenação, detalhe e filtro por período | 200; 2 vendas; filtro vazio no período passado |
| 25 | Cancelar venda e tentar cancelar novamente | 200 com estorno; segunda tentativa 409 |
| 26 | Alterar preço após a venda | Item mantém o preço e subtotal originais |
| 27 | Payload sem itens, quantidade zero e produto_id nulo | 422 |

### Evidência da execução

Anexar na entrega um print ou trecho do terminal com a saída `27 passed`. Para gerar novamente:

```powershell
python -m pytest -v | Tee-Object -FilePath docs/evidencia_pytest.txt
```

## 3. Testes manuais no Postman

### Preparação

1. Inicie a API:

   ```powershell
   python -m uvicorn app.main:app --reload
   ```

2. Confirme que `http://127.0.0.1:8000/health` responde `{"status":"ok",...}`.
3. No Postman, clique em **Import** e selecione `docs/postman_collection.json`.
4. Verifique a variável da coleção:
   - `base_url = http://127.0.0.1:8000`
   - `produto_id`, `venda_id` e `produto_descartavel_id` são preenchidos automaticamente.
5. Opcionalmente, limpe o banco para começar do zero: pare a API, apague `data/vendas.db` e reinicie.

### Execução pelo Collection Runner

1. Clique nos três pontos da coleção **API de Gestão de Produtos e Vendas**.
2. Selecione **Run**.
3. Mantenha a ordem das requisições, sem atraso entre elas.
4. Clique em **Run API de Gestão de Produtos e Vendas**.

Resultado esperado: **23 requisições executadas**, com os testes de cada requisição aprovados. Os cenários negativos (estoque insuficiente, produto inativo, cancelamento repetido e produto excluído) são considerados aprovados ao retornar **409** ou **404**, conforme o roteiro.

### Matriz de testes manuais

| Grupo | Requisição | Método e rota | Verificação | Status esperado |
|---|---|---|---|---|
| Sistema | Health check | GET `/health` | `status = ok` e banco conectado | 200 |
| Sistema | Swagger | GET `/docs` | Página HTML do Swagger | 200 |
| Produtos | Cadastrar | POST `/api/v1/produtos` | ID gerado, SKU `POSTMAN-*`, estoque 50 | 201 |
| Produtos | Consultar | GET `/api/v1/produtos/{id}` | Mesmo ID, estoque 50 | 200 |
| Produtos | Atualizar | PATCH `/api/v1/produtos/{id}` | Preço 199,90 | 200 |
| Produtos | Buscar | GET `/api/v1/produtos?busca=Postman` | Produto encontrado | 200 |
| Produtos | Filtrar | GET `/api/v1/produtos?categoria=...&ativo=true` | Itens ativos da categoria | 200 |
| Vendas | Registrar | POST `/api/v1/vendas` | Total 399,80, status CONCLUIDA | 201 |
| Estoque | Verificar baixa | GET `/api/v1/produtos/{id}` | Estoque 50 → 48 | 200 |
| Vendas | Detalhar | GET `/api/v1/vendas/{id}` | Item vendido e total | 200 |
| Vendas | Histórico | GET `/api/v1/vendas?limit=10` | Venda criada presente | 200 |
| Vendas | Filtrar status | GET `/api/v1/vendas?status=CONCLUIDA` | Somente vendas concluídas | 200 |
| Negativo | Estoque insuficiente | POST `/api/v1/vendas` com 999999 | Mensagem de estoque insuficiente | 409 |
| Estoque | Estoque intacto | GET `/api/v1/produtos/{id}` | Continua 48 | 200 |
| Vendas | Cancelar | PATCH `/api/v1/vendas/{id}/cancelar` | Status CANCELADA e data preenchida | 200 |
| Estoque | Estorno | GET `/api/v1/produtos/{id}` | Estoque volta para 50 | 200 |
| Negativo | Cancelar novamente | PATCH `/api/v1/vendas/{id}/cancelar` | Erro de venda já cancelada | 409 |
| Exclusão | Produto com venda | DELETE `/api/v1/produtos/{id}` | Sem corpo de resposta | 204 |
| Exclusão | Confirmar inativação | GET `/api/v1/produtos/{id}` | `ativo = false` | 200 |
| Negativo | Vender inativo | POST `/api/v1/vendas` | Produto inativo | 409 |
| Exclusão | Criar descartável | POST `/api/v1/produtos` | Produto sem vendas | 201 |
| Exclusão | Excluir sem vendas | DELETE `/api/v1/produtos/{id}` | Sem corpo de resposta | 204 |
| Exclusão | Confirmar exclusão | GET `/api/v1/produtos/{id}` | Produto não existe | 404 |

### Scripts de teste embutidos

Cada requisição da coleção possui scripts na aba **Tests**, por exemplo:

```js
const body = pm.response.json();

pm.test('Status 201 - venda registrada', () => {
  pm.response.to.have.status(201);
});

pm.test('Venda concluída com total de 399.80', () => {
  pm.expect(body.status).to.eql('CONCLUIDA');
  pm.expect(Number(body.total)).to.eql(399.80);
});

pm.collectionVariables.set('venda_id', body.id);
```

Isso permite executar toda a suíte com um clique e encadear as requisições por variáveis.

## 4. Alternativa com Insomnia

O Insomnia importa coleções Postman v2.1:

1. Abra o Insomnia.
2. **Application** → **Import** → **From File**.
3. Selecione `docs/postman_collection.json`.
4. Confirme o ambiente com `base_url = http://127.0.0.1:8000`.
5. Execute as requisições na ordem dos grupos. Os scripts de teste do Postman são exibidos como metadados; no Insomnia, valide manualmente os status indicados na matriz acima.
6. Para encadear IDs, copie o `id` retornado no cadastro para as requisições de venda ou crie variáveis de ambiente no Insomnia.

## 5. Testes rápidos com cURL

### Criar produto

```bash
curl -X POST http://127.0.0.1:8000/api/v1/produtos \
  -H "Content-Type: application/json" \
  -d '{"nome":"Produto cURL","categoria":"Testes","sku":"CURL-001","preco":10.00,"quantidade_estoque":5}'
```

### Registrar venda

```bash
curl -X POST http://127.0.0.1:8000/api/v1/vendas \
  -H "Content-Type: application/json" \
  -d '{"itens":[{"produto_id":1,"quantidade":6}]}'
```

Resposta esperada: HTTP 409 com `detail` informando `disponível 5, solicitado 6`.

### Consultar estoque

```bash
curl http://127.0.0.1:8000/api/v1/produtos/1
```

O estoque deve permanecer 5 após a tentativa bloqueada.

## 6. Checklist de evidências para a entrega

- [ ] Print da saída `27 passed` do pytest.
- [ ] Print do Swagger em `/docs` com as rotas e schemas.
- [ ] Print do Postman Collection Runner com as 23 requisições.
- [ ] Print de uma venda registrada com total e itens.
- [ ] Print do estoque antes e depois da venda.
- [ ] Print do erro 409 em venda sem estoque.
- [ ] Print do histórico de vendas.
- [ ] Print do `git log --oneline` mostrando os commits.
- [ ] Link do repositório público no GitHub.

## 7. Observações

- Os testes automatizados usam um banco em memória e não afetam `data/vendas.db`.
- Os testes do Postman usam a API real e gravam dados no banco local. Para uma apresentação limpa, recrie o banco antes da execução.
- Os cenários negativos são parte do plano de testes: retornar 409/404 é o comportamento correto, não uma falha.
- O horário das vendas é gravado em UTC; ao filtrar por data, use o formato ISO 8601.
