"""AG-UI shared state models.

These Pydantic models define the AgentContext that flows between
the Angular frontend and the ADK agent via AG-UI STATE_DELTA events.
"""

from typing import Any

from pydantic import BaseModel


class DataShape(BaseModel):
    rows: int
    columns: list[str]


class VisualizationState(BaseModel):
    chartType: str
    title: str
    surfaceId: str
    sourceQuery: str
    dataShape: DataShape
    interactive: bool = True


class QueryState(BaseModel):
    sql: str
    database: str = "analytics_db"
    rowCount: int
    executionTimeMs: int
    columns: list[str]


class AgentContext(BaseModel):
    currentVisualization: VisualizationState | None = None
    lastQuery: QueryState | None = None
    activeFilters: dict[str, Any] = {}
    dataSource: str = "postgresql"
    conversationIntent: str | None = None
