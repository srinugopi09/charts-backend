from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    database_url: str = "postgresql://analytics:localdev@localhost:5432/analytics_db"
    gemini_model: str = "gemini-2.0-flash"
    google_api_key: str = ""
    cors_origins: str = "http://localhost:4200"
    log_level: str = "INFO"
    session_db_url: str = ""

    # Database pool settings
    db_pool_size: int = 5
    db_max_overflow: int = 10

    # Query safety settings
    query_timeout_seconds: int = 30
    max_query_rows: int = 1000

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def session_db_url_async(self) -> str:
        """Async DB URL for DatabaseSessionService.

        Uses session_db_url if explicitly set, otherwise derives from
        database_url by swapping the driver to asyncpg.
        """
        if self.session_db_url:
            return self.session_db_url
        return self.database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


@lru_cache
def get_settings() -> Settings:
    return Settings()
