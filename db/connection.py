import logging
from functools import lru_cache

from sqlalchemy import create_engine, Engine

from config.settings import get_settings

logger = logging.getLogger(__name__)


@lru_cache
def get_engine() -> Engine:
    """Create and cache a SQLAlchemy engine with connection pooling."""
    settings = get_settings()
    engine = create_engine(
        settings.database_url,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
        pool_timeout=30,
        pool_pre_ping=True,
    )
    logger.info("Database engine created: pool_size=%d, max_overflow=%d", settings.db_pool_size, settings.db_max_overflow)
    return engine
