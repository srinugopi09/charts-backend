# Charts Backend — Agentic Analytics Chatbot

## Tech Stack
- **Framework:** FastAPI + uvicorn
- **AI Agent:** google-adk v1.24+ (Agent class, plain Python functions as tools)
- **Protocol Bridge:** ag-ui-adk v0.4+ (ADKAgent wrapper, SSE endpoint)
- **LLM:** Gemini via google-generativeai (API key auth for MVP)
- **Database:** PostgreSQL 15+ with SQLAlchemy 2.0 (read-only queries)
- **Validation:** Pydantic 2.0 + pydantic-settings
- **Package Manager:** uv (NOT pip). Dependencies in pyproject.toml.
- **Testing:** pytest + pytest-asyncio + httpx

## Commands
```bash
uv sync                                       # Install dependencies
uv sync --extra dev                            # Install with dev dependencies
uv run uvicorn main:app --reload --port 8080   # Start dev server
uv run pytest tests/unit/ -v                   # Run unit tests (no DB needed for validation tests)
uv run pytest tests/integration/ -v            # Run integration tests (needs PostgreSQL + seed data)
uv run pytest tests/ --ignore=tests/evals -v   # Run all non-eval tests
uv run python tests/evals/run_evals.py --all   # Run ADK agent evaluations (needs PostgreSQL + Gemini key)
```

## Local Dev Setup
```bash
# 1. Start PostgreSQL
docker run -d --name analytics-db -p 5432:5432 \
  -e POSTGRES_USER=analytics -e POSTGRES_PASSWORD=localdev \
  -e POSTGRES_DB=analytics_db postgres:15

# 2. Load seed data
psql -h localhost -U analytics -d analytics_db -f seed/seed_data.sql

# 3. Create .env from template and add your Gemini API key
cp .env.example .env

# 4. Start server
uv run uvicorn main:app --reload --port 8080
```

## Project Structure
Code lives at repo root (not in a backend/ subdirectory):
- `main.py` — FastAPI app, CORS, health check, AG-UI SSE endpoint (`POST /api/agent/run`)
- `config/settings.py` — Pydantic Settings (env-based config, singleton via `get_settings()`)
- `agents/orchestrator.py` — ADK Agent definition with Gemini model and all 9 tools
- `agents/prompts/orchestrator_system.txt` — System prompt (iterated independently of code)
- `tools/sql_tools.py` — `list_tables`, `describe_table`, `query_database` with SQL safety validation
- `tools/a2ui_tools.py` — 6 A2UI generation tools with `tool_context` for shared state updates
- `a2ui/schema.py` — A2UI v0.9 spec-compliant models (Component, CreateSurface, UpdateComponents, Payload)
- `a2ui/chart_builder.py` — Builders for Graph, KPICard, DataTable, RAG, Insight (spec-compliant)
- `a2ui/dashboard_builder.py` — CompositeDashboard builder with children.explicitList
- `a2ui/catalog.py` — Component type registry, catalog ID, and 5 color palettes
- `state/shared_state.py` — AgentContext, VisualizationState, QueryState Pydantic models
- `db/connection.py` — SQLAlchemy engine factory with connection pooling

## Key Conventions
- **Tools are plain Python functions** returning dicts — ADK auto-wraps as FunctionTool
- **`tool_context=None`** optional parameter on tools — ADK auto-injects ToolContext at runtime
- **A2UI payloads** follow v0.9 spec: `{"a2ui": true, "surfaceId": "...", "messages": [createSurface, updateComponents]}`
- **SQL safety**: reject DDL/DML keywords via regex, read-only transaction, statement timeout, max rows
- **Settings** accessed via `get_settings()` singleton — never use `os.getenv()` directly
- **ag-ui-adk** handles SSE streaming, event translation, session lifecycle automatically
- **hatchling** build backend — packages listed in `[tool.hatch.build.targets.wheel]`

## Database
- PostgreSQL with 9 seed tables (~797 rows of deterministic test data)
- Seed script: `seed/seed_data.sql`
- Tables: teams (10), projects (30), quarterly_revenue (72), monthly_revenue (216), monthly_metrics (95), deliverables (87), budget_breakdown (78), resource_allocation (159), incidents (50)

## API Endpoints
- `POST /api/agent/run` — AG-UI SSE endpoint (accepts RunAgentInput, returns event stream)
- `GET /health` — Health check with DB connectivity status

## Environment Variables
See `.env.example`. Key variables:
- `DATABASE_URL` — PostgreSQL connection string (default: local dev)
- `GOOGLE_API_KEY` — Gemini API key (required for agent to work)
- `GEMINI_MODEL` — Model identifier (default: gemini-2.0-flash)
- `CORS_ORIGINS` — Comma-separated allowed origins
- `LOG_LEVEL` — Python logging level (default: INFO)

## Testing
- **Unit tests** (48 tests, no DB): SQL validation, A2UI builders, state models, config
- **Integration tests** (19 tests, needs DB): SSE endpoint, DB connectivity, tool execution
- **ADK evals** (25 cases, needs DB + Gemini): SQL accuracy, tool selection, viz selection, multi-turn
- DB-dependent tests require PostgreSQL with seed data loaded
