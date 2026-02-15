# Frontend Integration Guide — Conversation Persistence

## Overview

The backend now persists all conversation events (user messages, agent responses, tool calls, A2UI charts) in PostgreSQL. The frontend can load full chat history on page reload or thread switch without relying on local storage.

---

## Endpoints

All endpoints require the `X-User-Id` header (placeholder auth — will be swapped for real auth later).

### Thread List (Sidebar)

```
GET /api/threads?limit=50&offset=0
```

**Response:**
```json
{
  "threads": [
    {
      "id": "80c70ae6-9316-44ad-9309-19e723094446",
      "user_id": "user-123",
      "title": null,
      "created_at": "2026-02-14T22:54:40+00:00",
      "updated_at": "2026-02-14T22:54:40+00:00"
    }
  ],
  "total": 1
}
```

- Sorted by `updated_at` descending (most recent first)
- Paginated via `limit` (1–100, default 50) and `offset` (default 0)
- Threads are **auto-created on first message** — no need to call `POST /api/threads` beforehand

### Chat History

```
GET /api/threads/{thread_id}/messages
```

**Response:**
```json
{
  "thread_id": "80c70ae6-9316-44ad-9309-19e723094446",
  "messages": [
    {
      "role": "user",
      "content": "Show me Q3 revenue"
    },
    {
      "role": "assistant",
      "content": "Let me query the quarterly revenue data for you.",
      "message_id": "msg-abc123"
    },
    {
      "role": "assistant",
      "content": "{\"sql_query\": \"SELECT * FROM quarterly_revenue WHERE quarter = 'Q3'\"}",
      "tool_call_name": "query_database",
      "tool_call_id": "tc-def456"
    },
    {
      "role": "tool",
      "content": "{\"columns\": [...], \"rows\": [...]}",
      "tool_call_id": "tc-def456",
      "event_data": { "a2ui": true, "surfaceId": "surface-1", "messages": [...] }
    },
    {
      "role": "assistant",
      "content": "Here's your Q3 revenue breakdown.",
      "message_id": "msg-ghi789"
    }
  ]
}
```

### Rename Thread

```
PATCH /api/threads/{thread_id}
Content-Type: application/json

{ "title": "Q3 Revenue Analysis" }
```

### Delete Thread

```
DELETE /api/threads/{thread_id}
```

Cascades — deletes all stored events and the ADK agent session.

### Send Message (unchanged)

```
POST /api/agent/run
Content-Type: application/json

{
  "threadId": "uuid",
  "runId": "uuid",
  "messages": [...],
  "state": {},
  "tools": [],
  "context": [],
  "forwardedProps": {}
}
```

Returns: SSE event stream (no changes to this endpoint).

---

## Message Types & Rendering

| `role` | `tool_call_name` | What it is | How to render |
|--------|-----------------|------------|---------------|
| `user` | — | User's message | Chat bubble (right side) |
| `assistant` | `null` | Agent's text response | Chat bubble (left side), render content as **markdown** |
| `assistant` | present (e.g. `query_database`) | Agent invoked a tool | Collapsible step indicator (e.g. "Queried database"), or hide |
| `tool` | — | Tool result | Check `event_data.a2ui` — see below |

### A2UI Detection (Charts & Dashboards)

Tool result messages may contain A2UI payloads (charts, KPI cards, dashboards). Detect via:

```typescript
if (message.role === 'tool' && message.event_data?.a2ui === true) {
  // Render A2UI component using:
  //   message.event_data.surfaceId
  //   message.event_data.messages  (createSurface + updateComponents)
} else {
  // Plain tool result — show as collapsible raw JSON or hide
}
```

---

## Frontend Flows

### Page Load / Refresh

```
1. GET /api/threads                          → populate sidebar
2. If a thread was previously selected:
   GET /api/threads/{thread_id}/messages     → render chat history
3. Ready for new messages via POST /api/agent/run
```

### Switch Thread

```
1. GET /api/threads/{thread_id}/messages     → render chat history
2. Ready for new messages via POST /api/agent/run
```

### New Conversation

```
1. Generate a new UUID on the frontend       → this becomes the threadId
2. User types a message
3. POST /api/agent/run with the new threadId → thread auto-created in backend
4. GET /api/threads                          → refresh sidebar (new thread appears)
```

### Delete Conversation

```
1. DELETE /api/threads/{thread_id}           → removes thread + all events + agent session
2. Remove from sidebar locally or re-fetch GET /api/threads
```

---

## FAQ (Frontend Team Questions)

### 1. A2UI `event_data.messages` format

**Answer: Option A — Backend wire format (flat properties).**

The A2UI payloads are stored exactly as the agent produced them. Components use **flat properties** with a `"component"` discriminator:

```json
{
  "a2ui": true,
  "surfaceId": "chart-a1b2c3d4",
  "messages": [
    {
      "createSurface": {
        "surfaceId": "chart-a1b2c3d4",
        "catalogId": "analytics_chatbot"
      }
    },
    {
      "updateComponents": {
        "surfaceId": "chart-a1b2c3d4",
        "components": [
          {
            "id": "root",
            "component": "Graph",
            "graphType": "bar",
            "title": "Revenue by Region",
            "data": { "labels": [...], "datasets": [...] },
            "xLabel": "Quarter",
            "yLabel": "Amount ($)",
            "interactive": false,
            "showLegend": true,
            "colorScheme": "default",
            "valuePrefix": "$",
            "valueSuffix": ""
          }
        ]
      }
    }
  ]
}
```

This is the same format as what arrives in the SSE stream. Your existing `flattenBackendComponent` transform applies identically whether rendering from a live SSE event or from a replayed history message. **No double-transformation risk.**

> **Important:** In the `TOOL_CALL_RESULT` SSE event, the `content` field is a **JSON string** (not an object). The frontend must `JSON.parse(event.content)` to get the A2UI object. In the `GET /api/threads/{id}/messages` response, `event_data` is already a parsed object — no extra parsing needed.

### 2. Does the agent use `initialMessages` from the request or its own persisted history?

**Answer: The agent uses its own persisted history. The frontend can stop sending full history.**

The ADK `DatabaseSessionService` stores all prior turns in PostgreSQL. When `runner.run_async()` is called with a `session_id`, the ADK Runner automatically loads the full conversation history from the session. The `_get_unseen_messages()` method in ag-ui-adk filters out already-processed messages, so only the latest user message is actually used.

**What the frontend can do now:**

```json
{
  "threadId": "existing-thread-uuid",
  "runId": "new-run-uuid",
  "messages": [
    { "role": "user", "content": "What was the total revenue?", "id": "msg_123" }
  ],
  "state": {},
  "tools": [],
  "context": [],
  "forwardedProps": {}
}
```

Instead of sending 50 messages of history, just send the new user message. The agent will still have full context from prior turns via the ADK session.

### 3. Message pagination

**Answer: Currently returns the full list. This is intentional for MVP.**

For most conversations (< 100 runs), the response size is manageable. If pagination becomes necessary for long conversations, the backend can add `limit`/`offset` params to `GET /api/threads/{id}/messages`. For now, the frontend should assume the full list is always returned.

### 4. Auto-title

**Answer: Option A — Frontend responsibility.**

The backend stores `title: null` by default. The frontend should:

1. After the first agent response completes, truncate the first user message (or generate a summary)
2. Call `PATCH /api/threads/{thread_id}` with the title

This keeps title generation logic in the frontend where the UX lives. The backend may add auto-titling later as an enhancement.

### 5. Chart JSON in SSE stream

**Answer: No change. Chart data flows through `TOOL_CALL_RESULT` events.**

A2UI payloads have always been returned as tool results (not text messages). The flow is:

```
Agent calls tool (e.g. generate_chart)
  → TOOL_CALL_START event
  → TOOL_CALL_ARGS event
  → TOOL_CALL_END event
  → TOOL_CALL_RESULT event  ← A2UI payload is in content (JSON string)
```

The agent may also emit a `TEXT_MESSAGE` describing the chart (e.g. "Here's your Q3 revenue chart."), but the chart data itself is always in `TOOL_CALL_RESULT`. This behavior is unchanged with persistence — the same events are stored and replayed.

---

## Notes

- **No `POST /api/threads` needed** before chatting. Threads are auto-created when the first message is sent to `POST /api/agent/run`.
- **Thread titles** are `null` by default. Use `PATCH /api/threads/{id}` to set a title (e.g. auto-generate from first message, or let user rename).
- **Messages are ordered** — the response from `GET /api/threads/{id}/messages` returns messages in chronological order across all runs in the thread.
- **Multi-turn conversations** work naturally — each `POST /api/agent/run` is a "run" within the thread. All runs are stitched together in the messages response.
- **`X-User-Id` header** is required on all requests. This is a placeholder for real authentication — the backend will eventually swap it for JWT/OAuth token validation.
