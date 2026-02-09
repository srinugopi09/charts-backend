# Backend Blueprint — Agentic Analytics Chatbot

## FastAPI | Google ADK | ag_ui_adk | Gemini | PostgreSQL

---

## 1. Product Overview

The backend serves as the AI agent layer that receives natural language questions from the Angular frontend via the AG-UI protocol, routes them to appropriate tools (database queries, data analysis), generates insights and visualization decisions, and streams back text responses alongside A2UI chart payloads — all over a single SSE connection.

### MVP Scope

- Single AG-UI SSE endpoint consumed by Angular frontend
- ADK orchestrator agent with Gemini LLM
- NL-to-SQL tool for PostgreSQL (read-only)
- Schema discovery tools (list tables, describe columns)
- A2UI JSON generation (agent decides visualization type and builds the payload)
- AG-UI shared state management (conversation context, current visualization, last query)
- Multi-turn conversation with session persistence
- No authentication for MVP (internal tool behind VPN)
- No data access restrictions (agent can query any table)

### Out of Scope for MVP

- Rally integration via pyral SDK (phase 2)
- REST API connector tools (phase 2)
- MCP server abstraction (phase 2+)
- Authentication / authorization
- Rate limiting
- Caching layer

---

## 2. Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                     FastAPI Application                   │
│                                                         │
│  ┌───────────────────────────────────────────────────┐  │
│  │              AG-UI Endpoint                        │  │
│  │              POST /api/agent/run                   │  │
│  │              Returns: SSE stream                   │  │
│  │                                                   │  │
│  │  Accepts: RunAgentInput (messages, state,          │  │
│  │           threadId, runId)                         │  │
│  │  Returns: AG-UI event stream (text, tool calls,    │  │
│  │           state deltas, custom A2UI events)        │  │
│  └──────────────────────┬────────────────────────────┘  │
│                         │                                │
│  ┌──────────────────────▼────────────────────────────┐  │
│  │              ag_ui_adk Adapter                      │  │
│  │                                                   │  │
│  │  - Translates RunAgentInput → ADK session/run      │  │
│  │  - Translates ADK events → AG-UI SSE events        │  │
│  │  - Manages session lifecycle                       │  │
│  │  - Passes shared state to/from agent               │  │
│  └──────────────────────┬────────────────────────────┘  │
│                         │                                │
│  ┌──────────────────────▼────────────────────────────┐  │
│  │              ADK Orchestrator Agent                  │  │
│  │              (LlmAgent — Gemini)                    │  │
│  │                                                   │  │
│  │  Responsibilities:                                 │  │
│  │  1. Understand the user's question                 │  │
│  │  2. Pick the right tool(s) to answer it            │  │
│  │  3. Execute tools (SQL query, schema lookup)       │  │
│  │  4. Analyze the returned data                      │  │
│  │  5. Decide the best visualization type             │  │
│  │  6. Generate A2UI JSON payload for charts          │  │
│  │  7. Provide text summary alongside the viz         │  │
│  │  8. Update shared state (current viz, last query)  │  │
│  │                                                   │  │
│  │  Tools registered:                                 │  │
│  │  - list_tables                                     │  │
│  │  - describe_table                                  │  │
│  │  - query_database (read-only SQL)                  │  │
│  │  - generate_chart (A2UI Graph payload)             │  │
│  │  - generate_kpi_card (A2UI KPICard payload)        │  │
│  │  - generate_data_table (A2UI DataTable payload)    │  │
│  │  - generate_dashboard (A2UI CompositeDashboard)    │  │
│  │  - generate_rag_indicator (A2UI RAGIndicator)      │  │
│  │  - generate_insight_card (A2UI InsightCard)        │  │
│  └──────────────────────┬────────────────────────────┘  │
│                         │                                │
│                    Tool Execution                         │
│                         │                                │
│              ┌──────────▼──────────┐                    │
│              │   PostgreSQL via    │                     │
│              │   SQLAlchemy        │                     │
│              │   (read-only)       │                     │
│              └─────────────────────┘                    │
│                                                         │
│  ┌───────────────────────────────────────────────────┐  │
│  │              Session Management                     │  │
│  │              ADK SessionService                     │  │
│  │              (in-memory for MVP, Cloud SQL later)   │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

---

## 3. Project Structure

```
backend/
├── main.py                         # FastAPI app, CORS, AG-UI endpoint
├── config/
│   ├── settings.py                 # Environment-based config (DB URL, Gemini model, etc.)
│   └── data_sources.yaml           # Data source registry (for future extensibility)
│
├── agents/
│   ├── orchestrator.py             # Root ADK LlmAgent definition
│   └── prompts/
│       └── orchestrator_system.txt # System instructions for the orchestrator
│
├── tools/
│   ├── sql_tools.py                # list_tables, describe_table, query_database
│   └── a2ui_tools.py              # generate_chart, generate_kpi_card, generate_data_table,
│                                   # generate_dashboard, generate_rag_indicator, generate_insight_card
│
├── a2ui/
│   ├── schema.py                   # A2UI JSON schema definitions and builders
│   ├── chart_builder.py            # Builds A2UI Graph payloads from query results
│   ├── dashboard_builder.py        # Builds CompositeDashboard payloads
│   └── catalog.py                  # Catalog definition (component types + property schemas)
│
├── state/
│   └── shared_state.py             # AgentContext schema (Pydantic model for AG-UI shared state)
│
├── db/
│   └── connection.py               # SQLAlchemy engine setup, connection pooling
│
├── tests/
│   ├── conftest.py                 # Shared fixtures: DB session, test client, agent runner
│   ├── unit/
│   │   ├── test_sql_tools.py       # SQL safety, query validation, result formatting
│   │   ├── test_a2ui_builders.py   # A2UI JSON structure, property mapping, node IDs
│   │   ├── test_shared_state.py    # Pydantic model validation, delta application
│   │   └── test_config.py          # Settings loading, defaults
│   ├── integration/
│   │   ├── test_api_endpoint.py    # SSE stream format, event ordering, error events
│   │   ├── test_db_connectivity.py # Connection pooling, read-only enforcement
│   │   └── test_tool_execution.py  # Tools against real database with seed data
│   └── evals/
│       ├── eval_config.yaml        # ADK evaluation configuration
│       ├── test_cases/
│       │   ├── sql_accuracy.yaml   # NL question → expected SQL patterns
│       │   ├── tool_selection.yaml # Question → expected tool sequence
│       │   ├── viz_selection.yaml  # Data pattern → expected chart type
│       │   └── multi_turn.yaml    # Conversation flows → expected behavior
│       └── run_evals.py            # Script to run ADK evaluations locally
│
├── seed/
│   └── seed_data.sql               # Test database seed script
│
├── Dockerfile
├── requirements.txt
└── .env.example
```

---

## 4. Dependencies

| Package | Purpose |
|---|---|
| `fastapi` | Web framework |
| `uvicorn` | ASGI server |
| `google-adk` | Agent Development Kit |
| `ag-ui-adk` | AG-UI adapter for ADK |
| `google-cloud-aiplatform` | Vertex AI / Gemini access (used when `GOOGLE_CLOUD_PROJECT` is set) |
| `google-generativeai` | Gemini API key access (used for local dev / MVP without GCP project) |
| `sqlalchemy` | Database connectivity and query execution |
| `psycopg2-binary` | PostgreSQL driver |
| `pydantic` | Data validation, shared state schema |
| `pydantic-settings` | Environment-based configuration |
| `python-dotenv` | Local env file loading |
| `pytest` | Test framework |
| `pytest-asyncio` | Async test support for FastAPI |
| `httpx` | Async test client for FastAPI endpoint tests |

### Future Dependencies (Not for MVP)

| Package | Purpose | Phase |
|---|---|---|
| `pyral` | Rally SDK | Phase 2 |
| `httpx` | Async REST API calls | Phase 2 |
| `ag-ui-mcp` or equivalent | MCP server integration | Phase 2+ |

---

## 5. Configuration

### Environment Variables

| Variable | Description | Example |
|---|---|---|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@host:5432/dbname` |
| `GEMINI_MODEL` | Gemini model identifier | `gemini-2.0-flash` |
| `GOOGLE_API_KEY` | Gemini API key (for local dev / MVP) | `AIzaSy...` |
| `CORS_ORIGINS` | Allowed origins | `http://localhost:4200,https://app.internal.com` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `SESSION_DB_URL` | Session storage (optional) | `sqlite:///sessions.db` or PostgreSQL URL |

**Gemini auth modes:**
- **MVP (API key):** Set `GOOGLE_API_KEY`. ADK uses the `google-generativeai` SDK. No GCP project needed.
- **Production (Vertex AI):** Set `GOOGLE_CLOUD_PROJECT` + `GOOGLE_CLOUD_LOCATION` instead of `GOOGLE_API_KEY`. ADK auto-detects and switches to the `vertexai` SDK. Requires GCP project with Vertex AI enabled.
- Switching between modes is a configuration change only — no code changes.

### Settings Model (Pydantic)

Define a `Settings` class using `pydantic-settings` that loads from environment variables with sensible defaults. All config accessed via a single settings instance — no scattered `os.getenv()` calls.

---

## 6. API Layer

### 6.1 Single Endpoint

```
POST /api/agent/run
Content-Type: application/json
Accept: text/event-stream

→ Returns: SSE stream of AG-UI events
```

**Request body** follows AG-UI's `RunAgentInput` schema:

| Field | Type | Description |
|---|---|---|
| `threadId` | `string` | Conversation session ID |
| `runId` | `string` | Unique run ID for this request |
| `messages` | `Message[]` | Full conversation history |
| `state` | `AgentContext` | Current shared state from frontend |
| `tools` | `Tool[]` | Frontend tools (empty for MVP) |

**Response** is an SSE stream. Each event is a JSON object with a `type` field matching one of AG-UI's event types (TEXT_MESSAGE_START, TEXT_MESSAGE_CONTENT, TOOL_CALL_START, STATE_DELTA, CUSTOM, RUN_FINISHED, etc.).

### 6.2 Health Check

```
GET /health
→ { "status": "healthy", "database": "connected", "gemini": "available" }
```

### 6.3 CORS

Allow origins from `CORS_ORIGINS` config. Allow all methods and headers for MVP.

---

## 7. ADK Agent Design

### 7.1 Orchestrator Agent

The orchestrator is a single `LlmAgent` that handles all user interactions. It uses Gemini as its LLM and has access to all tools.

**Agent configuration:**

| Setting | Value |
|---|---|
| `name` | `analytics_orchestrator` |
| `model` | Configured via `GEMINI_MODEL` env var (default: `gemini-2.0-flash`) |
| `tools` | All SQL tools + all A2UI generation tools |
| `instruction` | Detailed system prompt (see below) |

**Why a single agent (not multi-agent) for MVP:**

- The MVP has one data source (PostgreSQL) and one output format (A2UI)
- A single agent with multiple tools is simpler to debug and iterate on
- Multi-agent (with a SQL sub-agent, a visualization sub-agent, etc.) can be introduced in phase 2 when Rally and REST APIs are added
- The tool interface is already designed to be modular — splitting into sub-agents later is a refactor, not a rewrite

### 7.2 Orchestrator System Prompt

The system prompt is the most critical piece of the agent design. It must be stored in a separate file (`agents/prompts/orchestrator_system.txt`) so it can be iterated on independently of code.

**System prompt content areas:**

1. **Role definition**: "You are an enterprise analytics assistant that helps users explore and understand their data through natural language conversation."

2. **Workflow instructions**:
   - First, understand what the user is asking about
   - If needed, explore the database schema (list_tables, describe_table) before writing SQL
   - Write and execute a SQL query to answer the question
   - Analyze the results — look for patterns, outliers, trends
   - Decide the best visualization type based on data shape and user intent
   - Generate an A2UI visualization payload using the appropriate generation tool
   - Provide a concise text summary of the insight BEFORE the visualization
   - Update shared state with the current visualization and query details

3. **Visualization decision rules** (the agent uses these to pick chart types):

   | Data Pattern | Visualization |
   |---|---|
   | Time series (dates/months on one axis) | Line chart or area chart |
   | Comparison across categories (≤10) | Vertical bar chart |
   | Comparison across categories (>10) | Horizontal bar chart |
   | Part-of-whole (≤6 segments) | Pie or doughnut chart |
   | Part-of-whole (>6 segments) | Stacked bar chart |
   | Two numeric dimensions | Scatter plot |
   | Single aggregate value | KPI card |
   | Multiple KPIs | Multiple KPI cards in a CompositeDashboard |
   | Multiple related metrics | CompositeDashboard with charts + KPIs |
   | Detailed records | DataTable |
   | Status/health check | RAG indicator |
   | Key finding or pattern | InsightCard |

4. **SQL safety rules**:
   - Only write SELECT queries — never INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE, or any DDL/DML
   - Always include LIMIT (max 1000 rows) unless the user explicitly asks for all data
   - Use parameterized column/table names from schema discovery, never guess
   - If unsure about schema, use list_tables and describe_table first

5. **Multi-turn context rules**:
   - When the user says "drill down" or "show more detail", check the shared state for `currentVisualization.sourceQuery` and `activeFilters`
   - Build the drill-down query by adding WHERE clauses or GROUP BY refinements to the source query
   - When the user says "now show that as a [chart type]", re-use the same data but change the visualization type
   - When the user says "go back", restore the previous visualization from conversation history

6. **A2UI generation rules**:
   - Always set `interactive: true` on charts so users can drill down
   - Use the `default` color scheme unless the user requests specific colors
   - For CompositeDashboard, put KPI cards first (top row) and charts below
   - Chart titles should be descriptive but concise (e.g., "Revenue by Region — Q4 2025")
   - Always include axis labels on bar and line charts

7. **Shared state update rules**:
   - After generating a visualization, update `currentVisualization` with chart type, title, source query, and data shape
   - After executing a query, update `lastQuery` with SQL, row count, execution time
   - When user applies filters via drill-down, update `activeFilters`
   - Always set `dataSource` to "postgresql"

### 7.3 How the Agent Generates A2UI

The agent does NOT generate raw A2UI JSON directly. Instead, it calls structured A2UI generation tools that accept simple parameters and return properly formatted A2UI JSON. This is more reliable than having the LLM produce complex nested JSON.

**Flow:**
1. Agent decides: "This is a bar chart comparing revenue by region"
2. Agent calls `generate_chart(chart_type="bar", title="Revenue by Region", labels=["East","West",...], datasets=[...], x_label="Region", y_label="Revenue ($)")`
3. The tool returns a properly structured A2UI surface JSON
4. The ag_ui_adk adapter emits this as a `CUSTOM` event with name `a2ui_surface_update`
5. Frontend receives and renders it

---

## 8. Tool Specifications

### 8.1 SQL Tools

---

#### list_tables

**Purpose:** Returns all table names in the connected PostgreSQL database.

**Parameters:** None

**Returns:** List of table names as strings.

**Behavior:**
- Uses SQLAlchemy's `inspect()` to get table names
- Excludes system/internal schemas (pg_catalog, information_schema)
- Returns from the default schema (public) unless configured otherwise

---

#### describe_table

**Purpose:** Returns the schema of a specific table.

**Parameters:**

| Parameter | Type | Required | Description |
|---|---|---|---|
| `table_name` | `string` | Yes | The table to describe |

**Returns:** Object with table name, columns (name, type, nullable, primary key), and row count estimate.

**Behavior:**
- Uses SQLAlchemy `inspect()` for columns and primary keys
- Includes a rough row count estimate (from pg_stat_user_tables, not COUNT(*))
- Returns column types as human-readable strings (not SQLAlchemy types)

---

#### query_database

**Purpose:** Executes a read-only SQL query and returns structured results.

**Parameters:**

| Parameter | Type | Required | Description |
|---|---|---|---|
| `sql_query` | `string` | Yes | A SELECT SQL query |

**Returns:** Object with columns (list of names), rows (list of value arrays), row_count, and execution_time_ms.

**Safety enforcement:**
- Normalize the query (strip whitespace, uppercase first word)
- Reject if not starting with SELECT or WITH (for CTEs)
- Reject if contains INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE, GRANT, REVOKE (even in subqueries)
- Wrap execution in a read-only transaction
- Enforce a timeout (configurable, default 30 seconds)
- Enforce max rows (configurable, default 1000) — if query returns more, truncate and include a warning
- Log every executed query for audit

**Result format:**
- Convert all values to JSON-serializable types (dates → ISO strings, decimals → floats, etc.)
- Include column names as metadata
- Include execution time for transparency (shown to user via tool call display)

---

### 8.2 A2UI Generation Tools

These tools are called by the agent to produce A2UI payloads. They accept simple, structured parameters and return well-formed A2UI JSON. The LLM never writes raw A2UI JSON.

---

#### generate_chart

**Purpose:** Generates an A2UI `Graph` component payload.

**Parameters:**

| Parameter | Type | Required | Description |
|---|---|---|---|
| `chart_type` | `string` | Yes | One of: bar, line, pie, doughnut, area, radar, scatter, horizontalBar, stackedBar, stackedArea |
| `title` | `string` | Yes | Chart title |
| `labels` | `list[string]` | Yes | X-axis or segment labels |
| `datasets` | `list[object]` | Yes | Each: { label, data, backgroundColor?, borderColor? } |
| `x_label` | `string` | No | X-axis label |
| `y_label` | `string` | No | Y-axis label |
| `interactive` | `boolean` | No (default true) | Enable drill-down |
| `color_scheme` | `string` | No (default "default") | Named palette |

**Returns:** A2UI surface JSON with a single Graph node.

---

#### generate_kpi_card

**Purpose:** Generates an A2UI `KPICard` component payload.

**Parameters:**

| Parameter | Type | Required | Description |
|---|---|---|---|
| `label` | `string` | Yes | Metric name |
| `value` | `string or number` | Yes | Metric value |
| `unit` | `string` | No | Unit label |
| `trend` | `string` | No | "up", "down", or "flat" |
| `trend_value` | `string` | No | Delta value |
| `trend_period` | `string` | No | Comparison period |
| `status` | `string` | No | "good", "warning", "critical" |

**Returns:** A2UI surface JSON with a single KPICard node.

---

#### generate_data_table

**Purpose:** Generates an A2UI `DataTable` component payload.

**Parameters:**

| Parameter | Type | Required | Description |
|---|---|---|---|
| `title` | `string` | Yes | Table title |
| `columns` | `list[object]` | Yes | Each: { key, label, type, align? } |
| `rows` | `list[list]` | Yes | Row data arrays |
| `sortable` | `boolean` | No (default true) | Enable sorting |
| `filterable` | `boolean` | No (default true) | Enable filtering |
| `page_size` | `integer` | No (default 25) | Rows per page |

**Returns:** A2UI surface JSON with a single DataTable node.

---

#### generate_dashboard

**Purpose:** Generates an A2UI `CompositeDashboard` with multiple child components.

**Parameters:**

| Parameter | Type | Required | Description |
|---|---|---|---|
| `title` | `string` | Yes | Dashboard title |
| `kpis` | `list[object]` | No | List of KPI definitions (same fields as generate_kpi_card) |
| `charts` | `list[object]` | No | List of chart definitions (same fields as generate_chart) |
| `tables` | `list[object]` | No | List of table definitions (same fields as generate_data_table) |
| `layout` | `string` | No (default "auto") | "auto", "2-column", "3-column", "1-top-2-bottom" |

**Returns:** A2UI surface JSON with a CompositeDashboard root node containing child KPICard, Graph, and DataTable nodes.

**Node ID assignment:** Dashboard root gets `dashboard-{sanitized-title}`. Children get `kpi-0`, `kpi-1`, `chart-0`, `chart-1`, `table-0`, etc.

---

#### generate_rag_indicator

**Purpose:** Generates an A2UI `RAGIndicator` component payload.

**Parameters:**

| Parameter | Type | Required | Description |
|---|---|---|---|
| `label` | `string` | Yes | What this status is for |
| `status` | `string` | Yes | "red", "amber", or "green" |
| `detail` | `string` | No | Explanation |
| `metric` | `string` | No | Underlying metric value |
| `threshold` | `string` | No | What threshold triggered this |

**Returns:** A2UI surface JSON with a single RAGIndicator node.

---

#### generate_insight_card

**Purpose:** Generates an A2UI `InsightCard` component payload.

**Parameters:**

| Parameter | Type | Required | Description |
|---|---|---|---|
| `title` | `string` | Yes | Insight title |
| `body` | `string` | Yes | Insight text (markdown supported) |
| `icon` | `string` | No | "info", "warning", "success", "tip" |
| `priority` | `string` | No | "high", "medium", "low" |

**Returns:** A2UI surface JSON with a single InsightCard node.

---

### 8.3 A2UI JSON Structure

All A2UI generation tools produce a consistent wrapper structure:

```
{
  "a2ui_surface_update": true,        ← Flag for the AG-UI adapter to emit as CUSTOM event
  "surface": {
    "nodes": [                        ← Flat list of A2UI nodes (adjacency model)
      {
        "id": "unique-node-id",
        "type": "Graph",              ← Must match a type in the frontend catalog
        "properties": { ... },        ← Component-specific properties
        "children": ["child-id"]      ← Only for container components (CompositeDashboard)
      }
    ]
  }
}
```

The ag_ui_adk adapter detects the `a2ui_surface_update` flag in tool results and emits the payload as an AG-UI `CUSTOM` event with `name: "a2ui_surface_update"`.

---

## 9. AG-UI Shared State

### 9.1 State Schema (Pydantic Model)

Define the `AgentContext` as a Pydantic BaseModel. This schema is validated on every incoming request and updated via STATE_DELTA events.

**AgentContext:**

| Field | Type | Default | Description |
|---|---|---|---|
| `currentVisualization` | `VisualizationState \| None` | `None` | What's on the canvas |
| `lastQuery` | `QueryState \| None` | `None` | Last SQL executed |
| `activeFilters` | `dict[str, Any]` | `{}` | User-applied filters |
| `dataSource` | `str` | `"postgresql"` | Active data source |
| `conversationIntent` | `str \| None` | `None` | Agent's read on the overall goal |

**VisualizationState:**

| Field | Type | Description |
|---|---|---|
| `chartType` | `str` | Chart type displayed |
| `title` | `str` | Chart title |
| `a2uiNodeId` | `str` | A2UI node ID |
| `sourceQuery` | `str` | SQL that produced this data |
| `dataShape` | `DataShape` | { rows: int, columns: list[str] } |
| `interactive` | `bool` | Drill-down enabled |

**QueryState:**

| Field | Type | Description |
|---|---|---|
| `sql` | `str` | The SQL executed |
| `database` | `str` | Database name |
| `rowCount` | `int` | Rows returned |
| `executionTimeMs` | `int` | Execution duration |
| `columns` | `list[str]` | Column names |

### 9.2 How State Updates Flow

**Agent → Frontend (STATE_DELTA):**

After the agent executes a query and generates a visualization, it updates the shared state. The ag_ui_adk adapter emits this as a `STATE_DELTA` event containing a JSON Patch.

Example: Agent runs a query and generates a bar chart.

The STATE_DELTA event contains patches:
- Set `currentVisualization` to new VisualizationState
- Set `lastQuery` to new QueryState
- Clear `activeFilters` (fresh visualization)

**Frontend → Agent (on next runAgent call):**

When the user clicks a chart segment and triggers a drill-down, the Angular app updates `activeFilters` in its local shared state. On the next `runAgent()` call, the full state is sent in the request body. The agent reads `activeFilters` and `currentVisualization.sourceQuery` to build the drill-down query.

### 9.3 State in ADK

The ag_ui_adk adapter maps the AG-UI shared state to ADK's session state. The agent accesses it via `context.state` in tool functions. When the agent wants to update shared state, it returns state patches in its tool results, which the adapter translates to STATE_DELTA events.

---

## 10. Session Management

### 10.1 MVP Approach

- Use ADK's built-in `InMemorySessionService` for MVP
- Sessions are keyed by `threadId` from the AG-UI request
- Session contains: conversation history (messages), current state, tool execution history
- Sessions are lost on server restart (acceptable for MVP)

### 10.2 Production Upgrade Path

- Switch to ADK's `DatabaseSessionService` with Cloud SQL (PostgreSQL)
- Enables persistent conversations across server restarts
- Enables horizontal scaling (multiple Cloud Run instances share session state)
- Configuration change only — no code changes to agent or tools

---

## 11. Database Connectivity

### 11.1 SQLAlchemy Setup

- Create a single `engine` instance at startup using `create_engine(DATABASE_URL)`
- Use connection pooling (SQLAlchemy's default QueuePool)
- Pool size: 5 connections (configurable)
- Max overflow: 10 (configurable)
- Connection timeout: 30 seconds

### 11.2 Read-Only Enforcement

Multiple layers of safety:

1. **Application layer**: SQL tools validate query starts with SELECT/WITH, rejects any DDL/DML keywords
2. **Connection layer**: Execute queries within `SET TRANSACTION READ ONLY` or use a read-only database user
3. **Database layer**: The PostgreSQL user the app connects with should have SELECT-only grants (defense in depth)

### 11.3 Schema Discovery

The agent needs to know what tables and columns exist to write accurate SQL. Two approaches:

**Dynamic discovery (MVP):**
- Agent calls `list_tables` and `describe_table` tools as needed
- First time a user asks about data, agent explores the schema
- Schema info is available in the conversation context for follow-up questions

**Cached schema (optimization for later):**
- On startup, discover all table schemas and cache them
- Include the schema summary in the agent's system prompt
- Agent can write SQL immediately without tool calls for schema exploration
- Refresh cache on a schedule or on-demand

For MVP, use dynamic discovery. It's simpler and works well for the first interaction. The agent's multi-turn context means it only needs to discover schema once per conversation.

---

## 12. A2UI Generation Layer

### 12.1 Design Philosophy

The A2UI generation layer sits between the agent's tool calls and the AG-UI event stream. Its job is to produce valid, consistent A2UI JSON from simple structured inputs.

**Principles:**
- The LLM never writes raw A2UI JSON — it calls tools with simple parameters
- The generation layer handles all A2UI formatting, node IDs, adjacency lists, property mapping
- The generation layer validates output against the A2UI component schemas
- Each tool produces a self-contained A2UI surface (or a component within a dashboard surface)

### 12.2 Catalog Definition

Define the catalog as a Python data structure that mirrors the frontend's A2UI catalog. This serves as the source of truth for what components the agent can use and what properties each accepts.

**Catalog entries:**

| Type Name | Properties Schema | Description |
|---|---|---|
| `Graph` | graphType, title, data, xLabel, yLabel, interactive, showLegend, colorScheme | Universal chart |
| `KPICard` | label, value, unit, trend, trendValue, trendPeriod, status | Single metric |
| `DataTable` | title, columns, rows, sortable, filterable, pageSize, maxHeight | Interactive table |
| `RAGIndicator` | label, status, detail, metric, threshold | Status indicator |
| `InsightCard` | title, body, icon, priority | Text insight |
| `CompositeDashboard` | title, layout, children | Multi-component container |

The catalog definition is used:
1. In the agent's system prompt — to tell the LLM what components are available
2. In the A2UI generation tools — to validate properties before building JSON
3. As documentation — single source of truth between frontend and backend

### 12.3 Color Palette Application

The generation tools apply color palettes to chart datasets:

| Palette | When Applied |
|---|---|
| `default` | Default for all charts unless specified |
| `sequential` | When agent detects a sequential/gradient pattern |
| `diverging` | When data has positive/negative values |
| `status` | When data maps to RAG states |
| `categorical` | When >6 distinct categories |

Palette colors are defined in the backend and sent in the A2UI payload's `backgroundColor` property. This ensures consistent colors between backend intent and frontend rendering.

---

## 13. Error Handling

### 13.1 SQL Errors

| Error | Agent Behavior |
|---|---|
| Invalid SQL syntax | Agent receives error message, rewrites the query, retries (max 2 retries) |
| Table not found | Agent discovers schema via list_tables, corrects table name, retries |
| Column not found | Agent describes the table, corrects column name, retries |
| Query timeout | Agent simplifies query (add LIMIT, remove joins), retries |
| Connection error | Return error event to frontend: "Database unavailable" |

### 13.2 Agent Errors

| Error | Behavior |
|---|---|
| Gemini API error | Emit RUN_ERROR event with user-friendly message |
| Tool execution exception | Agent receives error, explains to user, suggests rephrasing |
| A2UI generation fails | Fall back to text-only response with the data |
| Invalid shared state | Log warning, continue with default empty state |

### 13.3 Request-Level Errors

| Error | HTTP Response |
|---|---|
| Invalid request body | 422 with validation errors |
| Internal server error | 500 + RUN_ERROR event in stream |
| Request timeout | 504 (Cloud Run handles this) |

---

## 14. Logging and Observability

### 14.1 Structured Logging

- Use Python's `logging` module with JSON formatter
- Log every agent run: run_id, thread_id, duration, tool calls made
- Log every SQL query: query text, execution time, row count
- Log every A2UI payload generated: component types, node count
- Log errors with full context

### 14.2 Key Metrics to Track (Future)

| Metric | Description |
|---|---|
| Agent response time | Time from request to RUN_FINISHED |
| SQL query execution time | Per-query duration |
| Tool call count per run | How many tools the agent used |
| Error rate | Percentage of runs ending in RUN_ERROR |
| Visualization type distribution | Which chart types are most generated |
| Token usage | Gemini input/output tokens per run |

---

## 15. Local Development Setup

Everything runs locally with no cloud dependency. Here is the full local stack:

### 15.1 Prerequisites

| Tool | Version | Purpose |
|---|---|---|
| Python | 3.12+ | Backend runtime |
| Node.js | 18+ | Angular CLI and dev server |
| Docker | Latest | PostgreSQL container |
| Gemini API key | — | LLM access (no GCP project needed) |

### 15.2 PostgreSQL via Docker

```
docker run -d \
  --name analytics-db \
  -p 5432:5432 \
  -e POSTGRES_USER=analytics \
  -e POSTGRES_PASSWORD=localdev \
  -e POSTGRES_DB=analytics_db \
  postgres:15

# Load seed data
psql -h localhost -U analytics -d analytics_db -f seed/seed_data.sql
```

### 15.3 Backend Startup

```
cd backend/
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Create .env from template
cp .env.example .env
# Edit .env:
#   DATABASE_URL=postgresql://analytics:localdev@localhost:5432/analytics_db
#   GOOGLE_API_KEY=your-gemini-api-key-here
#   GEMINI_MODEL=gemini-2.0-flash
#   CORS_ORIGINS=http://localhost:4200

uvicorn main:app --host 0.0.0.0 --port 8080 --reload
```

### 15.4 Frontend Startup

```
cd frontend/
npm install
ng serve
# → http://localhost:4200
```

### 15.5 Local Development Workflow

```
Terminal 1: Docker PostgreSQL (or local PG install)
Terminal 2: uvicorn main:app --reload          → http://localhost:8080
Terminal 3: ng serve                            → http://localhost:4200
Terminal 4: (optional) pytest / playwright      → run tests
```

### 15.6 Running Tests Locally

```
# Backend unit tests (no Gemini needed)
cd backend/
pytest tests/unit/ -v

# Backend integration tests (needs PostgreSQL with seed data)
pytest tests/integration/ -v

# Backend ADK evals (needs PostgreSQL + Gemini API key)
python tests/evals/run_evals.py --all

# Frontend E2E (needs all three services running)
cd frontend/
npx playwright test

# Frontend E2E with specific browser
npx playwright test --project=desktop

# Frontend E2E with UI mode (interactive debugging)
npx playwright test --ui
```

---

## 16. Deployment — Google Cloud (When Ready)

### 16.1 Cloud Run Configuration

| Setting | Value | Rationale |
|---|---|---|
| Container port | 8080 | FastAPI default |
| Min instances | 1 | Avoid cold starts for internal tool |
| Max instances | 5 | Scale for team usage |
| Memory | 1Gi | Sufficient for agent + SQLAlchemy |
| CPU | 1 | Sufficient for MVP load |
| Request timeout | 300s | Long SSE streams (agent may query multiple times) |
| Concurrency | 10 | Multiple users per instance |
| Session affinity | Enabled | Keep sessions on same instance (for in-memory sessions) |

### 16.2 Cloud SQL

- PostgreSQL 15+ on Cloud SQL
- Private IP (same VPC as Cloud Run)
- Connected via Cloud Run VPC connector or Cloud SQL Auth Proxy
- Smallest instance tier for MVP (db-f1-micro or db-g1-small)

### 16.3 Secret Manager

Store in Google Secret Manager:
- `DATABASE_URL` — PostgreSQL connection string
- `GEMINI_API_KEY` — if using API key auth (or use Vertex AI default credentials)

### 16.4 Dockerfile

- Base: `python:3.12-slim`
- Install dependencies from requirements.txt
- Copy application code
- Expose port 8080
- CMD: uvicorn with `--timeout-keep-alive 300` (for long SSE connections)

---

## 17. Extensibility Design (Phase 2 Preparation)

### 17.1 Adding Rally via pyral SDK

**Tool interface pattern:** Follow the same pattern as SQL tools — define tools as functions decorated with `@tool`, register them on the orchestrator agent.

**New tools to add:**

| Tool | Purpose |
|---|---|
| `list_rally_workspaces` | List available Rally workspaces |
| `search_rally_artifacts` | Query Rally for portfolio items, features, stories |
| `get_epic_details` | Get a specific epic with child stories and completion % |
| `get_iteration_metrics` | Get sprint/iteration metrics (velocity, burndown) |
| `get_release_status` | Get PI/release level status across epics |

**Agent prompt update:** Add Rally data source routing rules to the system prompt. The agent will need to decide whether a question is about SQL data or Rally data.

**No frontend changes needed** — Rally tools produce the same A2UI payloads via the same generation tools. A burndown chart from Rally uses the same `generate_chart` tool as a bar chart from SQL.

### 17.2 Adding REST API Connector

**Pattern:** Generic REST API tool that accepts a URL, method, headers, and body. Agent constructs the API call based on conversation context.

**Or:** Specific tools per API (more reliable) — e.g., `call_hr_api`, `call_finance_api` — each with known endpoints and response schemas.

### 17.3 Migration to MCP

When ready to adopt MCP for data source abstraction:

1. Wrap each data source (PostgreSQL, Rally, REST APIs) as an MCP server
2. Each MCP server exposes its tools via the MCP protocol
3. ADK discovers tools from MCP servers at startup
4. Remove native tool definitions, replace with MCP tool references
5. Adding a new data source = deploying a new MCP server + registering it

**No changes to A2UI generation** — the A2UI tools remain on the orchestrator. MCP handles data fetching; A2UI handles visualization. They're independent concerns.

### 17.4 Multi-Agent Architecture (Future)

When complexity warrants it, split the single orchestrator into:

| Agent | Responsibility |
|---|---|
| Router Agent | Understands user intent, routes to specialist |
| SQL Agent | NL-to-SQL, schema discovery, query optimization |
| Rally Agent | Rally-specific queries and metrics |
| Visualization Agent | Decides chart type, generates A2UI payloads |

Use ADK's `LlmAgent` transfer mechanism for routing between agents. The AG-UI adapter handles this transparently — the frontend doesn't need to know about the internal agent topology.

---

## 18. Testing Strategy — pytest + ADK Evaluations

### 18.1 Testing Approach

The backend has two complementary testing layers:

1. **pytest** — tests that the code works correctly (SQL safety, A2UI JSON structure, API format, DB connectivity)
2. **ADK evaluation framework** — tests that the agent behaves correctly (picks the right tools, writes correct SQL, chooses appropriate visualizations, handles multi-turn context)

Both layers run against a real PostgreSQL database loaded with seed data. ADK evals additionally call real Gemini (same tradeoffs as frontend E2E: slower, non-deterministic, costs tokens).

### 18.2 Test Prerequisites

| Dependency | Required For | How |
|---|---|---|
| PostgreSQL with seed data | All tests | Docker container with `seed_data.sql` loaded |
| Gemini API key | ADK evals only | Set in `.env` |
| FastAPI app | Integration tests | Started via `httpx.AsyncClient` with `app` passed directly |

pytest unit tests mock the database where possible. Integration tests and ADK evals use the real seeded database.

### 18.3 Shared Fixtures (`conftest.py`)

| Fixture | Scope | Description |
|---|---|---|
| `db_engine` | `session` | SQLAlchemy engine connected to test PostgreSQL |
| `db_session` | `function` | Transaction-scoped DB session, rolls back after each test |
| `test_client` | `session` | `httpx.AsyncClient` wrapping the FastAPI app |
| `seeded_db` | `session` | Ensures seed data is loaded before test suite runs |
| `agent_runner` | `session` | ADK agent instance configured for testing |
| `sample_state` | `function` | Fresh `AgentContext` Pydantic model with default values |

### 18.4 Unit Tests (pytest)

---

#### test_sql_tools.py — SQL Safety & Execution

| Test | Description | Assert |
|---|---|---|
| `test_select_query_allowed` | Execute a valid SELECT query | Returns results with columns and rows |
| `test_cte_query_allowed` | Execute a WITH ... SELECT query | Returns results (CTEs are valid read operations) |
| `test_insert_rejected` | Pass INSERT statement to query_database | Raises or returns error, query NOT executed |
| `test_update_rejected` | Pass UPDATE statement | Rejected |
| `test_delete_rejected` | Pass DELETE statement | Rejected |
| `test_drop_rejected` | Pass DROP TABLE statement | Rejected |
| `test_alter_rejected` | Pass ALTER TABLE statement | Rejected |
| `test_truncate_rejected` | Pass TRUNCATE statement | Rejected |
| `test_grant_rejected` | Pass GRANT statement | Rejected |
| `test_injection_in_subquery` | Pass `SELECT * FROM t WHERE x IN (DELETE FROM t)` | Rejected — DDL/DML keywords detected even in subqueries |
| `test_multistatement_rejected` | Pass `SELECT 1; DROP TABLE x` | Rejected — multi-statement queries not allowed |
| `test_query_timeout` | Execute a deliberately slow query (e.g., `pg_sleep`) | Returns timeout error, does not hang |
| `test_max_rows_enforced` | Query that returns >1000 rows | Result truncated to 1000, includes warning |
| `test_result_serialization` | Query with dates, decimals, NULLs | All values JSON-serializable (ISO dates, floats, nulls) |
| `test_list_tables` | Call list_tables tool | Returns list of table names from seed data |
| `test_describe_table` | Call describe_table with a known table | Returns columns with names, types, nullable flags |
| `test_describe_nonexistent_table` | Call describe_table with unknown name | Returns error, not exception |
| `test_query_returns_execution_time` | Execute any query | Result includes `execution_time_ms` > 0 |

---

#### test_a2ui_builders.py — A2UI JSON Structure

| Test | Description | Assert |
|---|---|---|
| `test_graph_bar_structure` | Generate a bar chart A2UI payload | Valid surface JSON with single Graph node, type="bar", has data/labels |
| `test_graph_line_structure` | Generate a line chart | Valid surface, type="line" |
| `test_graph_pie_structure` | Generate a pie chart | Valid surface, type="pie" |
| `test_graph_all_types` | Parameterized test for every `graphType` | Each type produces valid JSON |
| `test_graph_color_scheme_default` | Generate chart without color_scheme | `backgroundColor` populated with default palette colors |
| `test_graph_color_scheme_custom` | Generate chart with `color_scheme="sequential"` | Colors match sequential palette |
| `test_kpi_card_structure` | Generate a KPI card | Valid surface with KPICard node, has label + value |
| `test_kpi_card_with_trend` | Include trend fields | trend, trendValue, trendPeriod present in properties |
| `test_data_table_structure` | Generate a data table | Valid surface with DataTable node, columns and rows present |
| `test_data_table_column_types` | Include various column types | Each ColumnDef has key, label, type |
| `test_rag_indicator_structure` | Generate RAG indicator | Valid surface, status is one of red/amber/green |
| `test_insight_card_structure` | Generate insight card | Valid surface, body contains markdown text |
| `test_dashboard_structure` | Generate composite dashboard | Surface has dashboard root + child nodes, children IDs match |
| `test_dashboard_kpis_and_charts` | Dashboard with 2 KPIs + 1 chart | 3 child nodes, correct types |
| `test_node_ids_unique` | Generate a dashboard with multiple children | All node IDs are unique |
| `test_a2ui_surface_flag` | Any generation tool output | Result contains `a2ui_surface_update: true` flag |
| `test_invalid_chart_type_rejected` | Pass `chart_type="unknown"` | Validation error or fallback |
| `test_empty_data_handled` | Generate chart with empty labels/datasets | Returns graceful output (empty chart or error) |

---

#### test_shared_state.py — Pydantic State Validation

| Test | Description | Assert |
|---|---|---|
| `test_default_agent_context` | Create AgentContext with defaults | All fields have correct defaults (None, {}, "postgresql") |
| `test_visualization_state_roundtrip` | Create, serialize, deserialize VisualizationState | All fields preserved |
| `test_query_state_roundtrip` | Create, serialize, deserialize QueryState | All fields preserved |
| `test_partial_state_update` | Update only `lastQuery` leaving others unchanged | Other fields unchanged |
| `test_active_filters_merge` | Set filters, then add more | Filters merge (not replace) |
| `test_invalid_state_rejected` | Pass malformed state JSON | Pydantic validation error |

---

#### test_config.py — Configuration

| Test | Description |
|---|---|
| `test_settings_from_env` | Settings loads correctly from environment variables |
| `test_settings_defaults` | Default values used when env vars not set |
| `test_database_url_required` | Missing DATABASE_URL raises clear error |
| `test_cors_origins_parsed` | Comma-separated CORS_ORIGINS parsed into list |

### 18.5 Integration Tests (pytest)

---

#### test_api_endpoint.py — AG-UI SSE Endpoint

These tests call the actual FastAPI endpoint via `httpx.AsyncClient` and validate the SSE stream structure.

| Test | Description | Assert |
|---|---|---|
| `test_run_returns_sse` | POST to `/api/agent/run` with valid body | Response content-type is `text/event-stream` |
| `test_event_stream_starts_with_run_started` | Send a message | First event type is `RUN_STARTED` |
| `test_event_stream_ends_with_run_finished` | Send a message, consume full stream | Last event type is `RUN_FINISHED` |
| `test_text_message_events_present` | Send a simple question | Stream contains `TEXT_MESSAGE_START`, at least one `TEXT_MESSAGE_CONTENT`, and `TEXT_MESSAGE_END` |
| `test_tool_call_events_for_sql` | Send a data question | Stream contains `TOOL_CALL_START` and `TOOL_CALL_END` (agent used a tool) |
| `test_state_delta_emitted` | Send a question that triggers a viz | Stream contains at least one `STATE_DELTA` event |
| `test_a2ui_custom_event_emitted` | Send a question that triggers a chart | Stream contains a `CUSTOM` event with `name: "a2ui_surface_update"` |
| `test_invalid_request_returns_422` | POST with missing required fields | Returns 422 |
| `test_error_event_on_failure` | Send request that triggers agent error | Stream contains `RUN_ERROR` event |
| `test_health_endpoint` | GET `/health` | Returns 200 with status fields |

---

#### test_db_connectivity.py — Database Layer

| Test | Description | Assert |
|---|---|---|
| `test_connection_established` | Engine connects to test database | No exception |
| `test_read_only_enforcement` | Attempt INSERT via tool | Rejected at application layer |
| `test_connection_pool_reuse` | Execute 20 queries | Pool doesn't exceed configured max |
| `test_concurrent_queries` | Run 5 queries in parallel | All return results, no deadlocks |

---

#### test_tool_execution.py — Tools Against Real Database

| Test | Description | Assert |
|---|---|---|
| `test_list_tables_returns_seed_tables` | Call list_tables | Returns known seed table names |
| `test_describe_projects_table` | Describe the `projects` table | Returns expected columns (id, name, status, budget, etc.) |
| `test_query_counts_projects` | Execute `SELECT COUNT(*) FROM projects` | Returns known count from seed data |
| `test_query_with_aggregation` | Execute `SELECT region, SUM(revenue) FROM quarterly_revenue GROUP BY region` | Returns grouped results |
| `test_query_with_date_range` | Execute a time-filtered query | Returns correctly filtered rows |

### 18.6 ADK Agent Evaluations

ADK evaluations test agent behavior — the "thinking" layer that decides which tools to use, what SQL to write, and which visualization to produce. These run against real Gemini and the seeded database.

---

#### 18.6.1 Evaluation Configuration

**File:** `tests/evals/eval_config.yaml`

| Setting | Value | Rationale |
|---|---|---|
| Model | Same as production (`GEMINI_MODEL`) | Test with the model you deploy |
| Evaluation runs per test case | 3 | Run each case multiple times to account for non-determinism |
| Pass threshold | 2 out of 3 runs must pass | Allows for occasional LLM variation |
| Timeout per run | 60 seconds | Agent may make multiple tool calls |
| Database | Test PostgreSQL with seed data | Reproducible queries |

---

#### 18.6.2 Test Case Categories

Each test case is a YAML file with:
- `input`: The user's natural language question
- `conversation_history`: Optional prior messages (for multi-turn tests)
- `shared_state`: Optional initial AgentContext
- `expected`: What to evaluate (see below)

---

#### sql_accuracy.yaml — Does the Agent Write Correct SQL?

| Test Case | Input | Expected |
|---|---|---|
| Simple count | "How many projects are there?" | SQL contains `COUNT(*)` or `COUNT(id)` from `projects` table. Result is a number matching seed data. |
| Group by | "Show revenue by region" | SQL contains `GROUP BY region` and `SUM(revenue)` or similar aggregation |
| Time filter | "Show monthly metrics for the last 6 months" | SQL contains a date filter (WHERE clause on a date column) |
| Join query | "Show project names with their team assignments" | SQL joins `projects` with `resource_allocation` or `teams` |
| Top N | "What are the top 5 projects by budget?" | SQL contains `ORDER BY budget DESC LIMIT 5` |
| Conditional | "Show only at-risk projects" | SQL contains `WHERE status = 'at_risk'` or similar |

**Evaluation criteria:**
- Tool called: `query_database` was invoked
- SQL pattern: the generated SQL contains expected keywords/clauses (not exact match)
- Result correctness: returned data shape matches expectation (right number of columns, reasonable row count)

---

#### tool_selection.yaml — Does the Agent Pick the Right Tools?

| Test Case | Input | Expected Tool Sequence |
|---|---|---|
| Simple question about data | "How many projects are there?" | `query_database` → `generate_kpi_card` |
| Schema exploration | "What tables are available?" | `list_tables` (no visualization) |
| Column discovery | "What columns does the projects table have?" | `describe_table` (no visualization) |
| Chart question | "Show revenue by region" | `query_database` → `generate_chart` |
| Table request | "List all projects" | `query_database` → `generate_data_table` |
| Dashboard request | "Give me an overview of project health" | `query_database` (possibly multiple) → `generate_dashboard` |
| Status check | "What is the health status of each project?" | `query_database` → `generate_rag_indicator` or `generate_chart` |

**Evaluation criteria:**
- Required tools: the expected tools were called (in any order)
- No extra tools: agent didn't call unnecessary tools (e.g., shouldn't call generate_chart for a "list tables" request)
- Schema discovery first: for ambiguous table/column references, agent calls list_tables or describe_table before query_database

---

#### viz_selection.yaml — Does the Agent Choose the Right Visualization?

| Test Case | Input | Expected Viz Type |
|---|---|---|
| Category comparison (few) | "Compare revenue across 4 regions" | `Graph` with graphType `bar` or `horizontalBar` |
| Time series | "Show monthly revenue trend" | `Graph` with graphType `line` or `area` |
| Part of whole | "What percentage of budget does each department use?" | `Graph` with graphType `pie` or `doughnut` |
| Single metric | "What is the total revenue?" | `KPICard` |
| Record listing | "Show me all the incidents" | `DataTable` |
| Multiple KPIs | "Show total revenue, average budget, and project count" | `CompositeDashboard` with KPICard children |
| Mixed dashboard | "Give me a project overview with key metrics and a status chart" | `CompositeDashboard` with mix of KPICard and Graph children |

**Evaluation criteria:**
- A2UI payload emitted: a `CUSTOM` event with `a2ui_surface_update` was in the stream
- Component type: the root node type matches expected (flexible — `bar` or `horizontalBar` both acceptable)
- Data present: the chart/table has non-empty data

---

#### multi_turn.yaml — Does the Agent Handle Context Correctly?

| Test Case | Conversation Flow | Expected Behavior |
|---|---|---|
| Drill-down | Turn 1: "Show revenue by region" → Turn 2: "Drill into the West region" | Turn 2 SQL adds `WHERE region = 'West'` (or similar filter) to turn 1's query |
| Change viz type | Turn 1: "Show revenue by region as a bar chart" → Turn 2: "Show that as a table instead" | Turn 2 uses same data but outputs `DataTable` instead of `Graph` |
| Add filter | Turn 1: "Show all projects" → Turn 2: "Only show at-risk ones" | Turn 2 adds a status filter |
| Reference "that" | Turn 1: "What is total revenue?" → Turn 2: "Break that down by quarter" | Turn 2 groups revenue by quarter (understands "that" = revenue) |
| Shared state context | Turn 1 generates chart → shared state has `currentVisualization` → Turn 2 asks follow-up | Agent uses `sourceQuery` from shared state, not just message text |

**Evaluation criteria:**
- Context preserved: turn 2 response references or builds on turn 1 data
- SQL evolution: turn 2 SQL modifies turn 1 SQL (adds filters, changes grouping) rather than starting from scratch
- Shared state used: agent reads `activeFilters` or `currentVisualization` from provided state

---

### 18.7 Running Tests

#### pytest (unit + integration)

```
# Run all unit tests
pytest tests/unit/ -v

# Run all integration tests (requires running PostgreSQL with seed data)
pytest tests/integration/ -v

# Run all tests
pytest tests/ -v --ignore=tests/evals

# Run with coverage
pytest tests/ --cov=. --cov-report=html --ignore=tests/evals
```

#### ADK Evaluations

```
# Run all eval suites
python tests/evals/run_evals.py --all

# Run specific eval suite
python tests/evals/run_evals.py --suite sql_accuracy

# Run with verbose output (shows agent reasoning)
python tests/evals/run_evals.py --all --verbose

# Run with specific model override
python tests/evals/run_evals.py --all --model gemini-2.0-flash
```

### 18.8 Test Data Dependency

All tests (pytest and ADK evals) depend on the seed database. The seed script (`seed/seed_data.sql`) creates tables and inserts known data that tests assert against.

**Critical rule:** If the seed data changes, review all tests and eval cases that reference specific values, row counts, or table names. The seed script is the single source of truth for test data.

**Seed data requirements (minimum):**

| Table | Min Rows | Purpose |
|---|---|---|
| `projects` | 20 | Project listing, status filtering, budget analysis |
| `teams` | 8 | Team-based queries, joins |
| `monthly_metrics` | 120 (12 months × 10 projects) | Time series, trend analysis |
| `deliverables` | 50 | Status tracking, RAG indicators |
| `resource_allocation` | 80 | Team × project × month data |
| `incidents` | 30 | Severity filtering, date ranges |
| `quarterly_revenue` | 48 (4 quarters × 4 regions × 3 product lines) | Revenue analysis, category comparison |

### 18.9 Handling Non-Determinism in ADK Evals

Since evals call real Gemini, results will vary. Strategies for reliable evaluation:

1. **Run each case 3 times, require 2/3 to pass** — accounts for occasional LLM variation
2. **Pattern match, not exact match** — check SQL contains `GROUP BY region`, not exact query text
3. **Flexible viz type** — accept `bar` or `horizontalBar` as equivalent
4. **Structural assertions** — check "A2UI payload has a Graph node" not "the chart title is exactly X"
5. **Log full agent trace on failure** — include tool calls, SQL generated, A2UI payload, and agent reasoning for debugging
6. **Separate flaky tracking** — if a test case fails >50% of runs across multiple sessions, it's a prompt engineering issue, not a test issue
