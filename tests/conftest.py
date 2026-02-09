import os

import pytest
from sqlalchemy import create_engine, text

from config.settings import Settings


@pytest.fixture(scope="session")
def db_engine():
    """SQLAlchemy engine connected to test PostgreSQL."""
    url = os.environ.get("DATABASE_URL", "postgresql://analytics:localdev@localhost:5432/analytics_db")
    engine = create_engine(url, pool_pre_ping=True)
    yield engine
    engine.dispose()


@pytest.fixture(scope="session")
def seeded_db(db_engine):
    """Verify seed data is loaded before test suite runs."""
    with db_engine.connect() as conn:
        result = conn.execute(text("SELECT COUNT(*) FROM teams"))
        count = result.scalar()
        assert count > 0, "Seed data not loaded — run: psql -f seed/seed_data.sql"
    return db_engine


@pytest.fixture
def sample_settings():
    """Settings instance with test defaults."""
    return Settings(database_url="postgresql://analytics:localdev@localhost:5432/analytics_db")
