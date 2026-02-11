# Charts Backend

Agentic analytics chatbot backend — ask questions about your data in natural language and get charts, tables, and insights back via an SSE stream.

Built with **FastAPI** + **Google ADK** + **AG-UI** + **Gemini** + **PostgreSQL**.

## Prerequisites

Before you start, make sure these are installed on your machine:

| Tool | Version | What it's for | Install link |
|------|---------|---------------|--------------|
| **Python** | 3.11+ | Runtime | [python.org/downloads](https://www.python.org/downloads/) |
| **uv** | latest | Python package manager (replaces pip) | [docs.astral.sh/uv](https://docs.astral.sh/uv/getting-started/installation/) |
| **Docker** | latest | Runs PostgreSQL locally | [docker.com/get-docker](https://docs.docker.com/get-docker/) |
| **psql** | any | Loads seed data into PostgreSQL | Bundled with [PostgreSQL](https://www.postgresql.org/download/), or install standalone via `brew install libpq` (macOS) |
| **Gemini API key** | — | Powers the AI agent | [aistudio.google.com/apikey](https://aistudio.google.com/apikey) |

## Quick Start

### 1. Clone the repo

```bash
git clone https://github.com/srinugopi09/charts-backend.git
cd charts-backend
```

### 2. Start PostgreSQL

Run a PostgreSQL 15 container with Docker:

```bash
docker run -d --name analytics-db -p 5432:5432 \
  -e POSTGRES_USER=analytics \
  -e POSTGRES_PASSWORD=localdev \
  -e POSTGRES_DB=analytics_db \
  postgres:15
```

Verify it's running:

```bash
docker ps | grep analytics-db
```

### 3. Load seed data

This creates 9 tables with ~797 rows of sample analytics data:

```bash
psql -h localhost -U analytics -d analytics_db -f seed/seed_data.sql
```

When prompted for a password, enter `localdev`.

### 4. Configure environment variables

```bash
cp .env.example .env
```

Open `.env` and replace `your-gemini-api-key-here` with your actual Gemini API key:

```
GOOGLE_API_KEY=your-actual-key-here
```

### 5. Install dependencies

```bash
uv sync --extra dev
```

This installs both production and development dependencies (pytest, httpx, etc.).

### 6. Start the server

```bash
uv run uvicorn main:app --reload --port 8080
```

### 7. Verify it works

In a separate terminal:

```bash
curl http://localhost:8080/health
```

You should see:

```json
{"status": "healthy", "database": "connected"}
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/agent/run` | AG-UI SSE endpoint — send a message, receive a stream of agent events (text, tool calls, charts, tables) |
| `GET` | `/health` | Health check — returns app status and database connectivity |

### SSE endpoint usage

The `/api/agent/run` endpoint accepts an [AG-UI `RunAgentInput`](https://docs.ag-ui.com) payload and returns a Server-Sent Events stream. It's designed to be consumed by AG-UI compatible frontends.

## Project Structure

```
charts-backend/
├── main.py                              # FastAPI app, CORS, health check, SSE endpoint
├── config/
│   └── settings.py                      # Pydantic Settings (env-based config)
├── agents/
│   ├── orchestrator.py                  # ADK Agent with Gemini model and 9 tools
│   └── prompts/
│       └── orchestrator_system.txt      # System prompt for the agent
├── tools/
│   ├── sql_tools.py                     # list_tables, describe_table, query_database
│   └── a2ui_tools.py                    # 6 A2UI visualization generation tools
├── a2ui/
│   ├── schema.py                        # A2UI v0.9 spec-compliant Pydantic models
│   ├── chart_builder.py                 # Graph, KPICard, DataTable, RAG, Insight builders
│   ├── dashboard_builder.py             # CompositeDashboard builder
│   └── catalog.py                       # Component type registry and color palettes
├── state/
│   └── shared_state.py                  # AgentContext, VisualizationState, QueryState models
├── db/
│   └── connection.py                    # SQLAlchemy engine factory with connection pooling
├── seed/
│   └── seed_data.sql                    # Deterministic seed data (9 tables, ~797 rows)
├── tests/
│   ├── unit/                            # 48 tests — no database needed
│   ├── integration/                     # 19 tests — needs PostgreSQL + seed data
│   └── evals/                           # 25 eval cases — needs PostgreSQL + Gemini key
├── .env.example                         # Environment variable template
├── pyproject.toml                       # Dependencies and build config
└── Dockerfile                           # Production container image
```

## Environment Variables

All variables are configured via a `.env` file (loaded automatically by Pydantic Settings).

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://analytics:localdev@localhost:5432/analytics_db` | No (default works for local dev) |
| `GOOGLE_API_KEY` | Gemini API key for the AI agent | — | **Yes** |
| `GEMINI_MODEL` | Gemini model identifier | `gemini-2.0-flash` | No |
| `CORS_ORIGINS` | Comma-separated allowed origins | `http://localhost:4200` | No |
| `LOG_LEVEL` | Python logging level | `INFO` | No |
| `SESSION_DB_URL` | Optional session storage URL | — | No |
| `DB_POOL_SIZE` | SQLAlchemy connection pool size | `5` | No |
| `DB_MAX_OVERFLOW` | Max overflow connections beyond pool | `10` | No |
| `QUERY_TIMEOUT_SECONDS` | Max SQL query execution time | `30` | No |
| `MAX_QUERY_ROWS` | Max rows returned per query | `1000` | No |

## Seed Data

The seed script (`seed/seed_data.sql`) creates these tables:

| Table | Rows | Description |
|-------|------|-------------|
| `teams` | 10 | Departments with headcount and locations |
| `projects` | 30 | Projects with status, priority, budget, and spend |
| `quarterly_revenue` | 72 | Revenue by team per quarter |
| `monthly_revenue` | 216 | Revenue by team per month |
| `monthly_metrics` | 95 | Monthly KPIs (active users, NPS, etc.) |
| `deliverables` | 87 | Project deliverables with status tracking |
| `budget_breakdown` | 78 | Budget allocation by category |
| `resource_allocation` | 159 | Team member assignments to projects |
| `incidents` | 50 | Incident records with severity and resolution |

The data is deterministic (no randomness), so you'll always get the same results for the same queries.

To re-seed (drops and recreates all tables):

```bash
psql -h localhost -U analytics -d analytics_db -f seed/seed_data.sql
```

## Running Tests

### Unit tests (no database needed)

```bash
uv run pytest tests/unit/ -v
```

Tests SQL validation, A2UI builders, shared state models, and config — 48 tests.

### Integration tests (needs PostgreSQL + seed data)

```bash
uv run pytest tests/integration/ -v
```

Tests SSE endpoint, database connectivity, and tool execution — 19 tests.

### All tests (except evals)

```bash
uv run pytest tests/ --ignore=tests/evals -v
```

### Agent evaluations (needs PostgreSQL + Gemini key)

```bash
uv run python tests/evals/run_evals.py --all
```

Tests SQL accuracy, tool selection, visualization selection, and multi-turn conversations — 25 cases.

## Docker (Production)

Build the image:

```bash
docker build -t charts-backend .
```

Run it (pass your environment variables):

```bash
docker run -d -p 8080:8080 \
  -e DATABASE_URL=postgresql://analytics:localdev@host.docker.internal:5432/analytics_db \
  -e GOOGLE_API_KEY=your-key-here \
  charts-backend
```

> **Note:** Use `host.docker.internal` instead of `localhost` to connect to a PostgreSQL instance running on your host machine from inside the container.

## Troubleshooting

### `uv: command not found`

Install uv:

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or with Homebrew
brew install uv
```

Then restart your terminal.

### `psql: command not found`

On macOS:

```bash
brew install libpq
echo 'export PATH="/opt/homebrew/opt/libpq/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

On Ubuntu/Debian:

```bash
sudo apt-get install postgresql-client
```

### Port 5432 already in use

Another PostgreSQL instance is running. Either stop it or use a different port:

```bash
# Use port 5433 instead
docker run -d --name analytics-db -p 5433:5432 \
  -e POSTGRES_USER=analytics \
  -e POSTGRES_PASSWORD=localdev \
  -e POSTGRES_DB=analytics_db \
  postgres:15
```

Then update `DATABASE_URL` in your `.env`:

```
DATABASE_URL=postgresql://analytics:localdev@localhost:5433/analytics_db
```

### Health check shows `"database": "disconnected"`

1. Check the PostgreSQL container is running: `docker ps | grep analytics-db`
2. If stopped, restart it: `docker start analytics-db`
3. Verify your `DATABASE_URL` in `.env` matches the container's port

### Agent returns errors about missing API key

Make sure `GOOGLE_API_KEY` is set in your `.env` file with a valid Gemini key. You can get one at [aistudio.google.com/apikey](https://aistudio.google.com/apikey).

### `ModuleNotFoundError` when starting the server

Run `uv sync` to install dependencies. If you need dev dependencies too, use `uv sync --extra dev`.
