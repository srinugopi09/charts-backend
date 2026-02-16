# Code Review: charts-backend

**Reviewer perspective:** Senior Staff Engineer, Python
**Branches reviewed:**
- `feat/chart-value-prefix-suffix` (commit `5d426c4`) — base codebase
- `feat/persistent-sessions-threads` (commit `74bb664`) — persistent sessions feature (+989 LOC)

**Scope:** Full codebase review (~2,200 LOC source, ~800 LOC tests)

---

# Part 1: Base Codebase Review

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

# Part 2: Persistent Sessions Feature Review (`feat/persistent-sessions-threads`)

4 new commits adding ~989 LOC across 14 files. This is the core of the review — new feature adding conversation persistence, thread CRUD, auth scaffolding, and Gemini debug logging.

---

## Critical Issues

### 17. Authentication is completely open — `auth/dependencies.py`

```python
def get_current_user_id(request: Request) -> str:
    return request.headers.get("x-user-id", "anonymous")
```

Any client can impersonate any user by setting the `X-User-Id` header. This is explicitly called out as a placeholder, but the code is wired to **every thread endpoint** and to the **agent run endpoint** with no middleware guard, feature flag, or warning log. Someone will deploy this as-is.

**Risks:**
- Any user can read/delete/modify any other user's threads by sending `X-User-Id: victim-user`.
- The fallback to `"anonymous"` means all unauthenticated requests share a single identity, creating a data leak between anonymous users.
- There's no rate limiting — an attacker can enumerate all threads.

**Recommendation:**
- Add a `REQUIRE_AUTH` setting (default `True`). When enabled, reject requests without a valid auth token with 401.
- At minimum, log a startup WARNING when running with placeholder auth so it's visible in production logs.
- Never fall back to `"anonymous"` — return 401 instead.

### 18. Fire-and-forget event persistence can silently lose data — `persistent_agent.py:138`

```python
async for event in super().run(input_data):
    asyncio.create_task(
        _save_event_async(thread_id, run_id, sequence, event, user_id)
    )
    sequence += 1
    yield event
```

`asyncio.create_task()` fires tasks that are never awaited and never collected. If the server shuts down, restarts, or the event loop drains while tasks are in-flight, events are silently lost. There's also no backpressure — if the DB is slow, hundreds of tasks can pile up.

Similarly on line 129:
```python
asyncio.ensure_future(asyncio.get_running_loop().run_in_executor(
    None, _save_user_message_sync,
    thread_id, run_id, user_id, content,
))
```

`ensure_future` here is equivalent to `create_task` — fire-and-forget with no reference kept.

**Recommendation:**
- Keep references to tasks and await them after the stream completes (e.g., `await asyncio.gather(*pending_tasks, return_exceptions=True)`).
- Or use a bounded asyncio.Queue with a background consumer that flushes batches, so you can drain cleanly on shutdown.
- Register a `@app.on_event("shutdown")` handler that flushes pending writes.

### 19. Synchronous DB operations on the thread-pool executor with no bounded pool — `persistent_agent.py:84`

```python
await loop.run_in_executor(
    None, _save_event_sync, thread_id, run_id, sequence, event, user_id,
)
```

`None` uses the default `ThreadPoolExecutor`, which in Python 3.11 defaults to `min(32, os.cpu_count() + 4)` workers. Each call opens a **synchronous** DB connection via `get_engine()`. Under load (many concurrent SSE streams), this means:
- Up to 32+ threads competing for the SQLAlchemy connection pool (size 5, overflow 10 = 15 max).
- Pool exhaustion → 30s `pool_timeout` → `TimeoutError` → lost events (caught and logged but data is gone).

**Recommendation:**
- Use a dedicated `ThreadPoolExecutor` with a bounded size matching the DB pool.
- Or better: use `asyncpg` directly (you already have it as a dependency for `DatabaseSessionService`) and avoid the sync→async bridge entirely.

### 20. `threads` table name conflicts with seed data — `db/models.py:24`

```python
__tablename__ = "threads"
```

The seed data has a `teams` table (not `threads`), but `Base.metadata.create_all()` in `main.py` creates a `threads` table at startup. This is fine for now, but the existing `_INTERNAL_TABLES` set in `sql_tools.py` hides it from the LLM. The issue is that `Base.metadata.create_all()` also creates `ag_ui_events` plus whatever tables the ADK `DatabaseSessionService` needs — and those ADK tables (`sessions`, `events`, `app_states`, `user_states`) are created by the ADK library separately. Two systems managing schema on the same database is a recipe for migration conflicts.

**Recommendation:**
- Use Alembic for your application tables. `create_all()` is fine for prototyping but doesn't support migrations.
- Document which tables are owned by your app vs. the ADK library.

---

## Moderate Issues

### 21. `_ensure_thread_exists` runs on every first event — race condition — `persistent_agent.py:42-43`

```python
if sequence == 0:
    _ensure_thread_exists(conn, thread_id, user_id)
```

The user message persistence (`_save_user_message_sync`) also calls `_ensure_thread_exists`. Both fire concurrently (fire-and-forget). If the user message task runs after `sequence=0` but its `_ensure_thread_exists` races with the event task's `_ensure_thread_exists`, you get two concurrent `INSERT ... ON CONFLICT DO NOTHING` — which is fine due to the `ON CONFLICT` clause. But if the user message task runs *before* the event and creates the thread, then the event at `sequence=0` re-checks unnecessarily. This isn't a bug per se (idempotent upsert), but the logic suggests the author expected ordered execution when it's actually concurrent. It works by accident because of `ON CONFLICT DO NOTHING`, but the design intent is unclear.

### 22. Thread ownership check uses two separate connections — `api/threads.py:255-271`

```python
# Verify thread ownership
with engine.connect() as conn:
    owner = conn.execute(
        select(Thread.__table__.c.user_id).where(Thread.id == tid)
    ).scalar()

if owner is None:
    raise HTTPException(status_code=404, detail="Thread not found")
if owner != user_id:
    raise HTTPException(status_code=404, detail="Thread not found")

# Fetch all events in order
with engine.connect() as conn:
    rows = conn.execute(...)
```

Two separate connections means a TOCTOU race: the thread could be deleted between the ownership check and the event fetch. Use a single connection.

### 23. `uuid.UUID(thread_id)` without try/except — `api/threads.py:122, 157, 182, 214, 252`

```python
thread_id = uuid.UUID(body.thread_id) if body.thread_id else uuid.uuid4()
```

If the client sends a malformed UUID (e.g., `"not-a-uuid"`), this raises `ValueError` which FastAPI converts to a 500 Internal Server Error. It should be caught and returned as 422/400.

**Recommendation:** Add a Pydantic validator or wrap in try/except with a proper HTTP error.

### 24. `delete_thread` is async but other CRUD endpoints are sync — `api/threads.py:208`

```python
@router.delete("/{thread_id}", status_code=204)
async def delete_thread(...):
```

`list_threads`, `create_thread`, `get_thread`, `update_thread`, `get_thread_messages` are all sync `def`. `delete_thread` is `async def` because it awaits `_session_service.delete_session()`. The sync endpoints do blocking I/O (SQLAlchemy `engine.connect()`) which blocks the asyncio event loop.

**Recommendation:** Either make all endpoints `async` with `run_in_executor` for the DB calls, or make `delete_thread` sync too and handle the async session deletion differently. The inconsistency is confusing and the sync endpoints will cause performance issues under concurrent load.

### 25. Global mutable state via `set_session_service()` — `api/threads.py:64-70`

```python
_session_service = None

def set_session_service(service):
    global _session_service
    _session_service = service
```

Module-level global mutable state set from `main.py`. This makes the module untestable without importing `main.py` first (which triggers all the side effects). A FastAPI dependency or `app.state` would be cleaner and testable.

### 26. `PreciseTimestamp` monkey-patch is fragile — `main.py:20-30`

```python
from google.adk.sessions.schemas.shared import PreciseTimestamp

_original_load_dialect_impl = PreciseTimestamp.load_dialect_impl

def _patched_load_dialect_impl(self, dialect):
    if dialect.name == "postgresql":
        return dialect.type_descriptor(DateTime(timezone=True))
    return _original_load_dialect_impl(self, dialect)

PreciseTimestamp.load_dialect_impl = _patched_load_dialect_impl
```

Monkey-patching an internal class from a third-party library. This will silently break when `google-adk` updates the class path, renames it, or fixes the timezone issue themselves. There's no test for this patch.

**Recommendation:**
- Add a version guard: `assert google.adk.__version__ < "1.25"` (or whatever fixes it).
- File an issue upstream and reference it in a comment.
- Add a test that verifies the patch works.

### 27. Debug logging hardcoded to file — `main.py:46-52`

```python
handlers=[
    logging.StreamHandler(),
    logging.FileHandler("gemini_debug.log"),
],
...
logging.getLogger("google_adk.google.adk.models.google_llm").setLevel(logging.DEBUG)
```

Every startup writes to `gemini_debug.log` — even in production. This file grows unbounded (no rotation). The DEBUG level for the Gemini logger will dump full prompts and responses, which may contain PII or sensitive business data.

**Recommendation:**
- Gate debug logging behind `LOG_LEVEL=DEBUG` or a separate `GEMINI_DEBUG` env var.
- Use `RotatingFileHandler` if file logging is needed.
- Never log full LLM prompts/responses in production without explicit opt-in.

### 28. No tests for the entire persistent sessions feature

989 lines of new code with zero tests. The threads API has 5 CRUD endpoints + a message reconstruction endpoint, the `PersistentADKAgent` has event persistence logic with async fire-and-forget behavior, and the auth dependency is untested.

**Recommendation:** At minimum:
- Unit tests for `get_thread_messages` event reconstruction logic (the state machine in lines 278-341).
- Unit tests for UUID validation edge cases.
- Integration test for thread CRUD lifecycle.
- Test that `_INTERNAL_TABLES` filtering works correctly.

### 29. `updated_at` column doesn't auto-update — `db/models.py:30`

```python
updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
```

`onupdate=func.now()` is a SQLAlchemy ORM-level feature. It only fires when you update via the ORM (e.g., `session.query(Thread).filter(...).update(...)`). But all the code in `api/threads.py` uses **Core** (e.g., `conn.execute(update(Thread.__table__).values(...))`). The `onupdate` trigger won't fire for Core updates.

**Recommendation:** Use a PostgreSQL trigger (`CREATE TRIGGER ... BEFORE UPDATE ... SET updated_at = NOW()`) or switch to ORM-style updates.

---

## Minor Issues

### 30. `_save_event_sync` calls `get_engine()` on every invocation — `persistent_agent.py:39`

```python
engine = get_engine()
```

`get_engine()` is `@lru_cache` so this is just a dict lookup, but it's called from a thread-pool thread. The `@lru_cache` is not thread-safe in CPython (though in practice the GIL makes it safe for reads). It would be cleaner to pass the engine as a parameter or capture it once at `PersistentADKAgent.__init__`.

### 31. `main.py` is accumulating too many responsibilities

`main.py` now handles: settings, env var export, monkey-patching, logging config, debug logging, CORS, agent creation, session service creation, auth wiring, endpoint registration, router inclusion, table creation at startup, and health checks. This is becoming a "God module".

**Recommendation:** Extract startup concerns into separate modules (e.g., `app_factory.py`, `startup.py`).

### 32. Missing `asyncpg` in `pyproject.toml` dependencies

The `session_db_url_async` property generates a `postgresql+asyncpg://` URL, and `DatabaseSessionService` requires asyncpg. But `asyncpg` is not listed in `pyproject.toml` dependencies — it's presumably pulled in transitively by `google-adk`, which is fragile.

**Recommendation:** Add `asyncpg` as an explicit dependency.

### 33. `_INTERNAL_TABLES` hardcodes ADK table names — `sql_tools.py:31-34`

```python
_INTERNAL_TABLES = {
    "sessions", "events", "app_states", "user_states",
    "adk_internal_metadata", "threads", "ag_ui_events",
}
```

If google-adk changes its internal table names, the LLM will suddenly see them and try to query them. These should be discovered dynamically or asserted at startup.

### 34. Seed data `teams` table conflict risk

The seed data has a `teams` table. The ORM has a `threads` table. Both share the same DB. If a future migration or seed script is careless, `Base.metadata.create_all()` could interfere with seed tables if they're ever added to the ORM. Keep the ORM models and seed schema clearly separated.

---

## What's Done Well (Persistent Sessions Feature)

- **`ON CONFLICT DO NOTHING` for thread creation** — idempotent upsert is the right pattern for auto-creating threads on first message.
- **`_INTERNAL_TABLES` filtering** — hiding ADK/app tables from the LLM agent is a good guardrail. This prevents the agent from querying internal state.
- **Event reconstruction state machine** in `get_thread_messages` — the TEXT_MESSAGE_START → CONTENT → END and TOOL_CALL_START → ARGS → END reconstruction is correct and handles the streaming protocol properly.
- **Frontend integration documentation** — `docs/frontend-integration.md` is thorough, well-structured, and anticipates common frontend team questions. This is excellent communication.
- **Cascade delete** — `ForeignKey("threads.id", ondelete="CASCADE")` on `ag_ui_events` means thread deletion automatically cleans up events. Correct.
- **User message content extraction** — the fix in commit `055ac25` properly handles both `str` and `list` content types from AG-UI messages, with a fallback to `str()`.

---

# Combined Priority Summary

| Priority | Issue | File | Section |
|----------|-------|------|---------|
| **P0** | `SET LOCAL` / `SET TRANSACTION READ ONLY` may be no-ops without explicit transaction | `sql_tools.py:161-162` | Base |
| **P0** | Missing dangerous PostgreSQL functions from SQL blocklist | `sql_tools.py:22-25` | Base |
| **P0** | Authentication is completely open — any user can impersonate any other | `auth/dependencies.py` | Sessions |
| **P0** | Fire-and-forget event persistence silently loses data on shutdown | `persistent_agent.py:138` | Sessions |
| **P1** | Synchronous DB in thread pool with no bounded pool — pool exhaustion risk | `persistent_agent.py:84` | Sessions |
| **P1** | No tests for 989 lines of new persistent sessions code | — | Sessions |
| **P1** | Debug logging hardcoded to file, dumps LLM prompts/responses, no rotation | `main.py:46-52` | Sessions |
| **P1** | `updated_at` column won't auto-update via Core-style queries | `db/models.py:30` | Sessions |
| **P1** | Silent JSON parse failures in `_parse_json_param` | `a2ui_tools.py:27-36` | Base |
| **P1** | DB fixtures in root `conftest.py` break "no DB needed" promise for unit tests | `tests/conftest.py` | Base |
| **P2** | `uuid.UUID()` without try/except — malformed UUIDs cause 500s | `api/threads.py` | Sessions |
| **P2** | TOCTOU race in thread ownership check (two separate connections) | `api/threads.py:255-271` | Sessions |
| **P2** | Sync/async endpoint inconsistency (blocking I/O on event loop) | `api/threads.py` | Sessions |
| **P2** | `PreciseTimestamp` monkey-patch is fragile, untested, undocumented | `main.py:20-30` | Sessions |
| **P2** | Module-level side effects in `main.py` complicate testing | `main.py` | Base |
| **P2** | `interactive` defaults to `False` contradicting system prompt | `a2ui_tools.py:64` | Base |
| **P2** | Global mutable `_session_service` — untestable without importing main | `api/threads.py:64-70` | Sessions |
| **P3** | `asyncpg` not in explicit dependencies (transitive only) | `pyproject.toml` | Sessions |
| **P3** | `_INTERNAL_TABLES` hardcodes ADK table names | `sql_tools.py:31-34` | Sessions |
| **P3** | `main.py` God module — too many responsibilities | `main.py` | Sessions |
| **P3** | `psycopg2-binary` not recommended for production | `pyproject.toml` | Base |
