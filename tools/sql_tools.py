"""SQL tools for the analytics orchestrator agent.

These are plain Python functions that ADK auto-wraps as FunctionTool.
Each returns a dict so the agent can read the result.
"""

import logging
import re
import time
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import inspect, text
from sqlalchemy.exc import OperationalError, SQLAlchemyError

from config.settings import get_settings
from db.connection import get_engine

logger = logging.getLogger(__name__)

# Keywords that must never appear in a query (word-boundary match, case-insensitive)
_FORBIDDEN_KEYWORDS = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|TRUNCATE|GRANT|REVOKE|CREATE|EXEC)\b",
    re.IGNORECASE,
)

# Tables managed by ADK / the application — hidden from the agent
_INTERNAL_TABLES = {
    "sessions", "events", "app_states", "user_states",
    "adk_internal_metadata", "threads", "ag_ui_events",
}


def list_tables() -> dict:
    """Returns all user table names in the connected PostgreSQL database.

    Returns:
        Dictionary with 'tables' (list of table names) and 'count'.
    """
    engine = get_engine()
    insp = inspect(engine)
    tables = sorted(t for t in insp.get_table_names() if t not in _INTERNAL_TABLES)
    logger.info("list_tables: found %d tables", len(tables))
    return {"tables": tables, "count": len(tables)}


def describe_table(table_name: str) -> dict:
    """Returns the schema of a specific table including columns, types, and row count estimate.

    Args:
        table_name: The table to describe.

    Returns:
        Dictionary with table_name, columns (list of dicts), and row_count_estimate.
    """
    engine = get_engine()
    insp = inspect(engine)

    # Check table exists (excluding internal tables)
    available = [t for t in insp.get_table_names() if t not in _INTERNAL_TABLES]
    if table_name not in available:
        return {"error": f"Table '{table_name}' not found. Available tables: {', '.join(available)}"}

    # Get columns
    raw_columns = insp.get_columns(table_name)
    pk_constraint = insp.get_pk_constraint(table_name)
    pk_columns = set(pk_constraint.get("constrained_columns", []))

    columns = []
    for col in raw_columns:
        columns.append({
            "name": col["name"],
            "type": str(col["type"]),
            "nullable": col.get("nullable", True),
            "primary_key": col["name"] in pk_columns,
        })

    # Row count estimate from pg_stat_user_tables (fast, no full scan)
    row_count_estimate = 0
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT n_live_tup FROM pg_stat_user_tables WHERE relname = :table_name"),
                {"table_name": table_name},
            )
            row = result.fetchone()
            if row:
                row_count_estimate = int(row[0])
    except SQLAlchemyError:
        pass  # Non-critical; estimate stays 0

    logger.info("describe_table: %s — %d columns, ~%d rows", table_name, len(columns), row_count_estimate)
    return {
        "table_name": table_name,
        "columns": columns,
        "row_count_estimate": row_count_estimate,
    }


def _validate_query(sql_query: str) -> str | None:
    """Validate a SQL query for safety. Returns error message or None if valid."""
    stripped = sql_query.strip()

    if not stripped:
        return "Empty query"

    # Reject multi-statement queries
    if ";" in stripped:
        return "Multi-statement queries are not allowed (semicolons detected)"

    # First keyword must be SELECT or WITH
    first_word = stripped.split()[0].upper()
    if first_word not in ("SELECT", "WITH"):
        return f"Only SELECT queries are allowed. Got: {first_word}"

    # Scan for forbidden DDL/DML keywords anywhere in the query
    match = _FORBIDDEN_KEYWORDS.search(stripped)
    if match:
        return f"Forbidden keyword detected: {match.group(0).upper()}"

    return None


def _serialize_value(value):
    """Convert a database value to a JSON-serializable type."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def query_database(sql_query: str, tool_context=None) -> dict:
    """Executes a read-only SQL query and returns structured results.

    Only SELECT and WITH (CTE) queries are allowed. DDL/DML statements are rejected.
    Results are limited to the configured max rows (default 1000).

    Args:
        sql_query: A SELECT SQL query to execute.
        tool_context: ADK ToolContext (auto-injected by ADK runtime). Used to update shared state.

    Returns:
        Dictionary with columns, rows, row_count, execution_time_ms, and optionally truncated flag.
        On error, returns a dictionary with an 'error' key.
    """
    settings = get_settings()

    # Safety validation
    error = _validate_query(sql_query)
    if error:
        logger.warning("query_database rejected: %s — %s", error, sql_query[:200])
        return {"error": f"Query rejected: {error}"}

    engine = get_engine()
    start = time.perf_counter()

    try:
        with engine.connect() as conn:
            # Set statement timeout and read-only transaction
            conn.execute(text(f"SET LOCAL statement_timeout = '{settings.query_timeout_seconds * 1000}'"))
            conn.execute(text("SET TRANSACTION READ ONLY"))

            result = conn.execute(text(sql_query))
            columns = list(result.keys())

            # Fetch up to max_rows + 1 to detect truncation
            raw_rows = result.fetchmany(settings.max_query_rows + 1)
            truncated = len(raw_rows) > settings.max_query_rows
            if truncated:
                raw_rows = raw_rows[: settings.max_query_rows]

            # Serialize values
            rows = [[_serialize_value(v) for v in row] for row in raw_rows]

            elapsed_ms = int((time.perf_counter() - start) * 1000)
            logger.info(
                "query_database: %d rows in %dms — %s",
                len(rows),
                elapsed_ms,
                sql_query[:200],
            )

            result_dict = {
                "columns": columns,
                "rows": rows,
                "row_count": len(rows),
                "execution_time_ms": elapsed_ms,
            }
            if truncated:
                result_dict["truncated"] = True
                result_dict["warning"] = f"Results truncated to {settings.max_query_rows} rows"

            # Update shared state with query details
            if tool_context is not None:
                tool_context.state["lastQuery"] = {
                    "sql": sql_query,
                    "database": "analytics_db",
                    "rowCount": len(rows),
                    "executionTimeMs": elapsed_ms,
                    "columns": columns,
                }

            return result_dict

    except OperationalError as e:
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        err_str = str(e)
        if "statement timeout" in err_str.lower() or "canceling statement" in err_str.lower():
            logger.error("query_database timeout after %dms: %s", elapsed_ms, sql_query[:200])
            return {"error": f"Query timed out after {settings.query_timeout_seconds} seconds"}
        logger.error("query_database OperationalError: %s", err_str)
        return {"error": f"Database error: {err_str}"}
    except SQLAlchemyError as e:
        logger.error("query_database SQLAlchemyError: %s", str(e))
        return {"error": f"Database error: {str(e)}"}
