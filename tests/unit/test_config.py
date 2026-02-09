import os

import pytest

from config.settings import Settings


def test_settings_from_env(monkeypatch):
    """Settings loads correctly from environment variables."""
    monkeypatch.setenv("DATABASE_URL", "postgresql://test:test@localhost:5432/testdb")
    monkeypatch.setenv("GEMINI_MODEL", "gemini-1.5-pro")
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key-123")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")

    s = Settings()
    assert s.database_url == "postgresql://test:test@localhost:5432/testdb"
    assert s.gemini_model == "gemini-1.5-pro"
    assert s.google_api_key == "test-key-123"
    assert s.log_level == "DEBUG"


def test_settings_defaults(monkeypatch):
    """Default values used when env vars not set."""
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_MODEL", raising=False)
    monkeypatch.delenv("CORS_ORIGINS", raising=False)
    monkeypatch.delenv("LOG_LEVEL", raising=False)
    s = Settings(database_url="postgresql://x:x@localhost/db", _env_file=None)
    assert s.gemini_model == "gemini-2.0-flash"
    assert s.google_api_key == ""
    assert s.cors_origins == "http://localhost:4200"
    assert s.log_level == "INFO"
    assert s.db_pool_size == 5
    assert s.db_max_overflow == 10
    assert s.query_timeout_seconds == 30
    assert s.max_query_rows == 1000


def test_database_url_has_default():
    """DATABASE_URL has a sensible default for local dev."""
    s = Settings()
    assert "postgresql://" in s.database_url


def test_cors_origins_parsed():
    """Comma-separated CORS_ORIGINS parsed into list."""
    s = Settings(
        database_url="postgresql://x:x@localhost/db",
        cors_origins="http://localhost:4200, https://app.internal.com , http://localhost:3000",
    )
    origins = s.cors_origins_list
    assert len(origins) == 3
    assert origins[0] == "http://localhost:4200"
    assert origins[1] == "https://app.internal.com"
    assert origins[2] == "http://localhost:3000"
