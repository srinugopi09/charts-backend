"""Integration tests for tool functions against real seeded database.

Requires running PostgreSQL with seed data loaded.
"""

import pytest

from tools.sql_tools import list_tables, describe_table, query_database


class TestToolExecution:
    def test_list_tables_returns_seed_tables(self, seeded_db):
        result = list_tables()
        expected_tables = {
            "teams", "projects", "quarterly_revenue", "monthly_revenue",
            "monthly_metrics", "deliverables", "budget_breakdown",
            "resource_allocation", "incidents",
        }
        assert expected_tables.issubset(set(result["tables"]))

    def test_describe_projects_table(self, seeded_db):
        result = describe_table("projects")
        assert result["table_name"] == "projects"
        col_names = [c["name"] for c in result["columns"]]
        expected_cols = ["id", "name", "status", "priority", "budget", "actual_spend", "start_date"]
        for col in expected_cols:
            assert col in col_names, f"Missing column: {col}"

    def test_query_counts_projects(self, seeded_db):
        result = query_database("SELECT COUNT(*) as cnt FROM projects")
        assert "error" not in result
        assert result["rows"][0][0] == 30

    def test_query_with_aggregation(self, seeded_db):
        result = query_database(
            "SELECT region, SUM(revenue) as total FROM quarterly_revenue GROUP BY region ORDER BY total DESC"
        )
        assert "error" not in result
        assert "region" in result["columns"]
        assert result["row_count"] > 0

    def test_query_with_date_range(self, seeded_db):
        result = query_database(
            "SELECT COUNT(*) as cnt FROM projects WHERE start_date >= '2025-06-01'"
        )
        assert "error" not in result
        assert result["rows"][0][0] > 0
