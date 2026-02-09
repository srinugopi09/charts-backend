"""Tests for SQL tool functions: safety validation, execution, and result formatting.

These tests require a running PostgreSQL with seed data loaded.
"""

import pytest

from tools.sql_tools import list_tables, describe_table, query_database, _validate_query


# ---------------------------------------------------------------------------
# Query validation (no DB needed)
# ---------------------------------------------------------------------------

class TestQueryValidation:
    def test_select_allowed(self):
        assert _validate_query("SELECT * FROM projects") is None

    def test_cte_allowed(self):
        assert _validate_query("WITH cte AS (SELECT 1) SELECT * FROM cte") is None

    def test_insert_rejected(self):
        err = _validate_query("INSERT INTO projects (name) VALUES ('x')")
        assert err is not None
        assert "INSERT" in err.upper() or "SELECT" in err.upper()

    def test_update_rejected(self):
        err = _validate_query("UPDATE projects SET name = 'x'")
        assert err is not None

    def test_delete_rejected(self):
        err = _validate_query("DELETE FROM projects")
        assert err is not None

    def test_drop_rejected(self):
        err = _validate_query("DROP TABLE projects")
        assert err is not None

    def test_alter_rejected(self):
        err = _validate_query("ALTER TABLE projects ADD COLUMN foo TEXT")
        assert err is not None

    def test_truncate_rejected(self):
        err = _validate_query("TRUNCATE projects")
        assert err is not None

    def test_grant_rejected(self):
        err = _validate_query("GRANT ALL ON projects TO public")
        assert err is not None

    def test_injection_in_subquery(self):
        err = _validate_query("SELECT * FROM projects WHERE id IN (DELETE FROM projects)")
        assert err is not None
        assert "DELETE" in err.upper()

    def test_multistatement_rejected(self):
        err = _validate_query("SELECT 1; DROP TABLE projects")
        assert err is not None
        assert "semicolon" in err.lower() or "multi" in err.lower()


# ---------------------------------------------------------------------------
# Tool execution (requires PostgreSQL with seed data)
# ---------------------------------------------------------------------------

class TestListTables:
    def test_list_tables(self, seeded_db):
        result = list_tables()
        assert "tables" in result
        assert "count" in result
        assert result["count"] >= 9
        assert "projects" in result["tables"]
        assert "teams" in result["tables"]
        assert "quarterly_revenue" in result["tables"]


class TestDescribeTable:
    def test_describe_table(self, seeded_db):
        result = describe_table("projects")
        assert result["table_name"] == "projects"
        assert len(result["columns"]) >= 8
        col_names = [c["name"] for c in result["columns"]]
        assert "id" in col_names
        assert "name" in col_names
        assert "status" in col_names
        assert "budget" in col_names
        # Check column structure
        id_col = next(c for c in result["columns"] if c["name"] == "id")
        assert id_col["primary_key"] is True
        assert "type" in id_col

    def test_describe_nonexistent_table(self, seeded_db):
        result = describe_table("nonexistent_table_xyz")
        assert "error" in result
        assert "not found" in result["error"].lower()


class TestQueryDatabase:
    def test_select_query_allowed(self, seeded_db):
        result = query_database("SELECT COUNT(*) as cnt FROM projects")
        assert "error" not in result
        assert result["columns"] == ["cnt"]
        assert result["row_count"] == 1
        assert result["rows"][0][0] == 30

    def test_cte_query_allowed(self, seeded_db):
        result = query_database("WITH cte AS (SELECT id FROM teams) SELECT COUNT(*) as cnt FROM cte")
        assert "error" not in result
        assert result["rows"][0][0] == 10

    def test_insert_rejected(self):
        result = query_database("INSERT INTO projects (name, status, priority, budget, start_date) VALUES ('x', 'on_track', 'low', 0, '2025-01-01')")
        assert "error" in result

    def test_update_rejected(self):
        result = query_database("UPDATE projects SET name = 'hacked'")
        assert "error" in result

    def test_delete_rejected(self):
        result = query_database("DELETE FROM projects")
        assert "error" in result

    def test_drop_rejected(self):
        result = query_database("DROP TABLE projects")
        assert "error" in result

    def test_alter_rejected(self):
        result = query_database("ALTER TABLE projects ADD COLUMN hacked TEXT")
        assert "error" in result

    def test_truncate_rejected(self):
        result = query_database("TRUNCATE projects")
        assert "error" in result

    def test_grant_rejected(self):
        result = query_database("GRANT ALL ON projects TO public")
        assert "error" in result

    def test_injection_in_subquery(self):
        result = query_database("SELECT * FROM projects WHERE id IN (DELETE FROM projects RETURNING id)")
        assert "error" in result

    def test_multistatement_rejected(self):
        result = query_database("SELECT 1; DROP TABLE projects")
        assert "error" in result

    def test_query_timeout(self, seeded_db):
        """Deliberately slow query should return timeout error."""
        result = query_database("SELECT pg_sleep(60)")
        assert "error" in result
        err_lower = result["error"].lower()
        assert "timed out" in err_lower or "timeout" in err_lower or "cancel" in err_lower

    def test_max_rows_enforced(self, seeded_db):
        """Query returning more rows than max should be truncated."""
        # Generate a large result set via cross join
        result = query_database(
            "SELECT a.id, b.id FROM projects a CROSS JOIN projects b CROSS JOIN projects c"
        )
        assert "error" not in result
        assert result["row_count"] <= 1000
        assert result.get("truncated") is True

    def test_result_serialization(self, seeded_db):
        """Dates, decimals, and NULLs should be JSON-serializable."""
        result = query_database(
            "SELECT start_date, budget, end_date FROM projects WHERE end_date IS NULL LIMIT 1"
        )
        assert "error" not in result
        row = result["rows"][0]
        # start_date should be ISO string
        assert isinstance(row[0], str)
        # budget should be float (from Decimal)
        assert isinstance(row[1], (int, float))
        # end_date NULL should be None
        assert row[2] is None

    def test_query_returns_execution_time(self, seeded_db):
        result = query_database("SELECT 1 as val")
        assert "error" not in result
        assert "execution_time_ms" in result
        assert result["execution_time_ms"] >= 0
