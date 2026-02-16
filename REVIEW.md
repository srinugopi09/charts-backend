# Code Review: charts-backend

**Reviewer perspective:** Senior Staff Engineer, Python
**Branch:** `feat/chart-value-prefix-suffix` (at commit `5d426c4`)
**Scope:** Full codebase review (~1,200 LOC source, ~800 LOC tests)

---

## Architecture & Design — Generally Solid

The overall structure is clean and appropriate for an MVP. Flat module layout, clear separation between tools/builders/schema/state, and the ADK plain-function convention is followed consistently.

---

## Critical Issues

### 1. SQL Injection via `text()` without bind parameters — `sql_tools.py:164`

```python
result = conn.execute(text(sql_query))
```

The query string from the LLM is passed directly to `text()`. The regex-based blocklist (`_FORBIDDEN_KEYWORDS`) is the only defense. This is a **defense-in-depth gap**:

- The regex is trivially bypassable. `SELECT` + a CTE with `COPY` or `pg_read_file()` or `lo_import()` are not blocked. PostgreSQL has many functions that can read/write the filesystem (`pg_read_file`, `pg_ls_dir`, `COPY ... TO`).
- `COPY` is not in the forbidden list.
- Comments can break the regex: `SE/**/LECT`, or `UPDATE` embedded in a string literal won't match word boundaries but real injections could restructure around the blocklist.

**Recommendation:** The `SET TRANSACTION READ ONLY` on line 162 is the real safety net and is good. But you should also:
- Use a dedicated read-only PostgreSQL role (not the same user that created the schema).
- Add `COPY`, `EXECUTE`, `CALL`, `DO`, `IMPORT`, `EXPORT` to the blocklist.
- Consider using `pg_stat_statements` or similar to audit queries.

### 2. `SET LOCAL` outside a transaction block — `sql_tools.py:161-162`

```python
conn.execute(text(f"SET LOCAL statement_timeout = '{settings.query_timeout_seconds * 1000}'"))
conn.execute(text("SET TRANSACTION READ ONLY"))
```

`SET LOCAL` only lasts until the end of the current transaction, but SQLAlchemy's `engine.connect()` uses **autocommit** by default in SQLAlchemy 2.0. Without an explicit `conn.begin()`, the `SET LOCAL` and `SET TRANSACTION READ ONLY` may have no effect or may raise an error depending on your psycopg2/SQLAlchemy version.

**Recommendation:** Wrap in an explicit transaction:
```python
with engine.connect() as conn:
    with conn.begin():
        conn.execute(text(...))  # SET LOCAL
        conn.execute(text(...))  # SET TRANSACTION READ ONLY
        result = conn.execute(text(sql_query))
```

This is the difference between your read-only guard *actually working* or silently being a no-op.

### 3. Semicolon check is too naive — `sql_tools.py:102`

```python
if ";" in stripped:
    return "Multi-statement queries are not allowed (semicolons detected)"
```

This rejects `SELECT * FROM foo WHERE name = 'a;b'` (a valid query with a semicolon inside a string literal). It also doesn't handle `$$`-quoted strings or `E'...'` escapes.

For an LLM-generated query this is probably acceptable (the LLM is unlikely to produce string literals with semicolons), but it's worth documenting as a known limitation or using a proper SQL parser.

---

## Moderate Issues

### 4. Module-level side effects in `main.py:10-16`

```python
settings = get_settings()

if settings.google_api_key:
    os.environ.setdefault("GOOGLE_API_KEY", settings.google_api_key)

from agents.orchestrator import orchestrator_agent  # noqa: E402
```

Module-level `os.environ` mutation and a conditional import make testing harder (you can't import `main` without triggering Gemini SDK initialization). The `noqa: E402` is a code smell — you're working around import order because of the side effect.

**Recommendation:** Move agent initialization behind a factory or a `@lru_cache` lazy init, similar to `get_engine()`. This also makes the test fixtures cleaner.

### 5. `@lru_cache` on `get_settings()` and `get_engine()` — not test-friendly

`@lru_cache` means you can never swap settings in tests without calling `get_settings.cache_clear()`. The `conftest.py` creates a `sample_settings` fixture, but no test code actually patches the singleton. If someone writes a test that calls `get_engine()`, they'll get the cached production engine pointing at localhost.

**Recommendation:** Consider a dependency-injection pattern or at minimum document that `get_settings.cache_clear()` must be called between test runs with different configs.

### 6. `conftest.py` — DB fixtures load for unit tests

The `conftest.py` at `tests/conftest.py` (session scope) tries to create a `db_engine` and `seeded_db` fixture that connects to PostgreSQL. Since it's at the root `tests/` level, it's active even for `tests/unit/` runs. This causes errors: unit tests in `test_sql_tools.py` that use the `seeded_db` fixture fail when no DB is available.

**Recommendation:** Move DB fixtures into `tests/integration/conftest.py`, or guard them with a `pytest.skip` if the DB is unreachable. The CLAUDE.md says "no DB needed" for unit tests, but the test structure contradicts this — 9 of the "unit tests" actually need a DB.

### 7. `_parse_json_param` silently swallows errors — `a2ui_tools.py:27-36`

```python
except (json.JSONDecodeError, TypeError):
    return default
```

If the LLM produces malformed JSON for `datasets`, `columns`, etc., this silently returns `[]` and the builder will produce an empty/broken chart with no error. The agent has no signal that something went wrong.

**Recommendation:** Return an `{"error": "Invalid JSON in parameter: ..."}` dict instead of silently falling back, so the LLM can retry.

### 8. `dashboard_builder.py` — KPI snake_case normalization is fragile (lines 44-49)

```python
for key in ("unit", "trend", "trendValue", "trend_value", "trendPeriod", "trend_period", "status"):
    camel = key.replace("_v", "V").replace("_p", "P")
```

This ad-hoc camelCase conversion only handles `_v` and `_p`. If any future property has `_s` or `_d` it'll break. Also, the loop iterates both `trendValue` and `trend_value` — since `.replace("_v", "V")` applied to `"trendValue"` produces `"trendValue"` (no-op), and applied to `"trend_value"` produces `"trendValue"`, this works by accident.

**Recommendation:** Use a small generic `snake_to_camel` utility, or just normalize the input once at the top.

### 9. No input validation on builder parameters

- `build_rag_surface` accepts any string for `status` (not just `"red"`, `"amber"`, `"green"`).
- `build_insight_surface` accepts any string for `icon` and `priority`.
- `build_kpi_surface` accepts any string for `trend` and `status`.
- Chart `interactive` defaults to `False` in `build_chart_surface` but the system prompt says "Always set interactive: true". The default is misleading.

**Recommendation:** Add validation with enums or `Literal` types. The Pydantic schema models (`RAGIndicatorProperties`, etc.) are defined in `a2ui/schema.py` but never used for validation — they're just documentation. Wire them up.

### 10. Health check does an import inside the function — `main.py:56-58`

```python
async def health():
    ...
    from sqlalchemy import text
    from db.connection import get_engine
```

If `sqlalchemy` isn't installed, the health check silently returns `db_status = "disconnected"` instead of failing loudly at startup. Since sqlalchemy is a core dependency, just import it at module level.

---

## Minor Issues

### 11. `generate_chart` parameter `interactive` defaults to `False` — `a2ui_tools.py:64`

The system prompt explicitly says "Always set interactive: true on charts". Having the code default to `False` means if the LLM omits the parameter, you get the wrong behavior. Default should be `True`.

### 12. Schema models defined but unused

`a2ui/schema.py` defines `A2UIPayload`, `GraphProperties`, `KPICardProperties`, `DataTableProperties`, etc. — but the builders in `chart_builder.py` and `dashboard_builder.py` construct raw dicts by hand. The Pydantic models aren't used for construction or validation anywhere. They're dead code.

**Recommendation:** Either use them (construct models, then call `.model_dump()`) or remove them. Dead code is worse than no code — it gives false confidence that validation is happening.

### 13. `_serialize_value` doesn't handle `timedelta`, `uuid.UUID`, or `memoryview`

PostgreSQL can return these types. `timedelta` from `INTERVAL` columns, `UUID` from `uuid` columns. They'll pass through unserializable and cause JSON encoding failures downstream.

### 14. Logging format uses em-dash — `main.py:20`

```python
format="%(asctime)s %(levelname)s %(name)s — %(message)s",
```

That `—` is a Unicode em-dash (U+2014), not a regular hyphen. This can cause issues with log parsers, grep, and monitoring tools that expect ASCII.

### 15. No `__all__` exports

None of the modules define `__all__`. For a package that's distributed via hatchling, this means `from tools import *` would import everything including internals like `_validate_query` and `_serialize_value`.

### 16. `psycopg2-binary` in production dependencies

`psycopg2-binary` is explicitly discouraged for production by the psycopg2 maintainers. It bundles its own libpq which can have version mismatches. Use `psycopg2` (source build) in production or migrate to `psycopg` (v3).

---

## What's Done Well

- **SQL safety layering**: Regex blocklist + `SET TRANSACTION READ ONLY` + statement timeout + row limits. Multiple defenses, even if each has gaps individually.
- **A2UI spec compliance**: The envelope structure (createSurface + updateComponents) is consistent and well-tested.
- **System prompt engineering**: Well-structured with decision matrices, explicit rules, and anti-patterns. The single-response rule is clearly articulated.
- **Test coverage for builders**: The parametrized chart type tests and envelope assertions are thorough.
- **Color palette design**: The cycling behavior in `get_palette` is clean.
- **Separation of concerns**: Tools -> builders -> schema is a good layering.
- **Deterministic seed data**: Enables consistent, reproducible test results.

---

## Summary of Priorities

| Priority | Issue | File |
|----------|-------|------|
| **P0** | `SET LOCAL` / `SET TRANSACTION READ ONLY` may be no-ops without explicit transaction | `sql_tools.py:161-162` |
| **P0** | Missing dangerous PostgreSQL functions from SQL blocklist (`COPY`, `pg_read_file`, `DO`) | `sql_tools.py:22-25` |
| **P1** | Silent JSON parse failures in `_parse_json_param` | `a2ui_tools.py:27-36` |
| **P1** | DB fixtures in root `conftest.py` break "no DB needed" promise for unit tests | `tests/conftest.py` |
| **P1** | Schema Pydantic models defined but never used for validation | `a2ui/schema.py` |
| **P2** | Module-level side effects in `main.py` complicate testing | `main.py:10-16` |
| **P2** | `interactive` defaults to `False` contradicting system prompt | `a2ui_tools.py:64` |
| **P2** | No input validation on enum-like parameters (RAG status, icon, priority) | `chart_builder.py` |
| **P3** | `psycopg2-binary` not recommended for production | `pyproject.toml` |
| **P3** | Ad-hoc snake_case normalization in dashboard builder | `dashboard_builder.py:44-49` |
