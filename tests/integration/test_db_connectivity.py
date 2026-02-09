"""Integration tests for database connectivity layer.

Requires running PostgreSQL with seed data.
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor

import pytest
from sqlalchemy import text

from db.connection import get_engine
from tools.sql_tools import query_database


class TestDBConnectivity:
    def test_connection_established(self, seeded_db):
        """Engine connects to test database without error."""
        engine = get_engine()
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            assert result.scalar() == 1

    def test_read_only_enforcement(self, seeded_db):
        """INSERT via tool function should be rejected at application layer."""
        result = query_database("INSERT INTO teams (name, department, headcount, location) VALUES ('Evil', 'Hacking', 1, 'Nowhere')")
        assert "error" in result

    def test_connection_pool_reuse(self, seeded_db):
        """Execute many queries — pool should not exceed configured max."""
        engine = get_engine()
        for _ in range(20):
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
        # If we get here without error, the pool handled 20 sequential connections
        pool = engine.pool
        assert pool.checkedin() <= engine.pool.size() + engine.pool.overflow()

    def test_concurrent_queries(self, seeded_db):
        """Run queries in parallel — all should succeed."""
        def run_query(i):
            return query_database(f"SELECT {i} as val")

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(run_query, i) for i in range(5)]
            results = [f.result() for f in futures]

        for i, result in enumerate(results):
            assert "error" not in result
            assert result["rows"][0][0] == i
