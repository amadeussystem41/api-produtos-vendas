"""Configuração do banco de dados e sessão do SQLAlchemy."""

from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings


class Base(DeclarativeBase):
    """Classe base dos modelos ORM."""


def _preparar_diretorio_sqlite(database_url: str) -> None:
    """Garante que a pasta do arquivo SQLite exista antes de criar o engine."""
    prefixo = "sqlite:///"
    if not database_url.startswith(prefixo):
        return

    caminho = database_url.removeprefix(prefixo)
    if not caminho or caminho == ":memory:":
        return

    Path(caminho).parent.mkdir(parents=True, exist_ok=True)


_preparar_diretorio_sqlite(settings.database_url)

_connect_args = (
    {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
)

engine = create_engine(
    settings.database_url,
    connect_args=_connect_args,
    future=True,
)

if settings.database_url.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def _habilitar_chaves_estrangeiras(dbapi_connection, _) -> None:
        """Ativa a verificação de chaves estrangeiras no SQLite."""
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


def get_db() -> Generator[Session, None, None]:
    """Dependency do FastAPI que fornece uma sessão e a encerra ao final."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def criar_tabelas() -> None:
    """Cria as tabelas no banco configurado."""
    # Importa os modelos para registrá-los no metadata do SQLAlchemy.
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
