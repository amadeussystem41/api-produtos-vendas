"""Ponto de entrada da API de Gestão de Produtos e Vendas."""

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.core.config import settings
from app.core.exceptions import APIError
from app.database import criar_tabelas
from app.dependencies import DbSession
from app.routers import produtos, vendas

DESCRICAO_API = """
API REST para gerenciamento de produtos e vendas, com controle automático
de estoque e documentação interativa gerada pelo Swagger/OpenAPI.

### Principais recursos

* **Produtos**: cadastro, consulta, busca, paginação, atualização e exclusão.
* **Vendas**: registro transacional, cálculo automático do total, baixa de
  estoque, histórico, consulta e cancelamento com estorno.
* **Regras de negócio**: bloqueio de vendas sem estoque, de produtos inativos
  e de SKUs duplicados. Uma venda com vários itens é totalmente revertida se
  qualquer item for inválido.

### Como testar

1. Cadastre um produto em `POST /api/v1/produtos`.
2. Registre uma venda em `POST /api/v1/vendas` usando o `id` retornado.
3. Consulte o estoque atualizado em `GET /api/v1/produtos/{produto_id}`.
4. Veja o histórico em `GET /api/v1/vendas`.

A coleção do Postman está em `docs/postman_collection.json`.
"""

TAGS_METADATA = [
    {
        "name": "Sistema",
        "description": "Informações gerais, documentação e verificação de saúde da API.",
    },
    {
        "name": "Produtos",
        "description": "Cadastro e manutenção do catálogo de produtos e do estoque.",
    },
    {
        "name": "Vendas",
        "description": "Registro de vendas, histórico e cancelamento com estorno de estoque.",
    },
]


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Cria as tabelas automaticamente na inicialização da aplicação."""
    criar_tabelas()
    yield


app = FastAPI(
    title=settings.app_name,
    description=DESCRICAO_API,
    version=settings.app_version,
    summary="API REST com FastAPI, SQLAlchemy e Swagger.",
    contact={
        "name": "Equipe do projeto",
        "url": "https://github.com/",
    },
    license_info={"name": "MIT", "url": "https://opensource.org/licenses/MIT"},
    openapi_tags=TAGS_METADATA,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    swagger_ui_parameters={
        "defaultModelsExpandDepth": -1,
        "docExpansion": "list",
        "displayRequestDuration": True,
        "filter": True,
        "syntaxHighlight.theme": "obsidian",
    },
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(APIError)
async def tratar_erro_de_negocio(_: Request, exc: APIError) -> JSONResponse:
    """Converte exceções de negócio no formato padrão de erro da API."""
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.mensagem})


app.include_router(produtos.router, prefix="/api/v1")
app.include_router(vendas.router, prefix="/api/v1")


@app.get("/", tags=["Sistema"], summary="Página inicial da API")
def raiz() -> dict[str, str]:
    """Apresenta os links principais da aplicação."""
    return {
        "mensagem": "API de Gestão de Produtos e Vendas em funcionamento.",
        "versao": settings.app_version,
        "documentacao_swagger": "/docs",
        "documentacao_redoc": "/redoc",
        "openapi": "/openapi.json",
        "saude": "/health",
    }


@app.get("/health", tags=["Sistema"], summary="Verificar saúde da API")
def verificar_saude(db: DbSession) -> dict[str, str]:
    """Verifica se a API está no ar e se o banco responde."""
    db.execute(text("SELECT 1"))
    return {
        "status": "ok",
        "banco_de_dados": "conectado",
        "versao": settings.app_version,
    }
