"""Configurações centrais da aplicação."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configurações carregadas de variáveis de ambiente ou do arquivo .env."""

    app_name: str = "API de Gestão de Produtos e Vendas"
    app_version: str = "1.0.0"
    database_url: str = "sqlite:///./data/vendas.db"
    cors_origins: str = "*"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origins_list(self) -> list[str]:
        """Converte a lista de origens separadas por vírgula em uma lista."""
        return [origem.strip() for origem in self.cors_origins.split(",") if origem.strip()]


@lru_cache
def get_settings() -> Settings:
    """Retorna uma instância única das configurações."""
    return Settings()


settings = get_settings()
