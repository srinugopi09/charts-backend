"""Tests for AG-UI shared state Pydantic models."""

import pytest
from pydantic import ValidationError

from state.shared_state import AgentContext, VisualizationState, QueryState, DataShape


class TestAgentContext:
    def test_default_agent_context(self):
        ctx = AgentContext()
        assert ctx.currentVisualization is None
        assert ctx.lastQuery is None
        assert ctx.activeFilters == {}
        assert ctx.dataSource == "postgresql"
        assert ctx.conversationIntent is None

    def test_visualization_state_roundtrip(self):
        viz = VisualizationState(
            chartType="bar",
            title="Revenue by Region",
            surfaceId="chart-abc123",
            sourceQuery="SELECT region, SUM(revenue) FROM quarterly_revenue GROUP BY region",
            dataShape=DataShape(rows=4, columns=["region", "sum"]),
            interactive=True,
        )
        data = viz.model_dump()
        restored = VisualizationState(**data)
        assert restored.chartType == "bar"
        assert restored.title == "Revenue by Region"
        assert restored.surfaceId == "chart-abc123"
        assert restored.dataShape.rows == 4
        assert restored.dataShape.columns == ["region", "sum"]
        assert restored.interactive is True

    def test_query_state_roundtrip(self):
        qs = QueryState(
            sql="SELECT COUNT(*) FROM projects",
            database="analytics_db",
            rowCount=1,
            executionTimeMs=42,
            columns=["count"],
        )
        data = qs.model_dump()
        restored = QueryState(**data)
        assert restored.sql == "SELECT COUNT(*) FROM projects"
        assert restored.rowCount == 1
        assert restored.executionTimeMs == 42
        assert restored.columns == ["count"]

    def test_partial_state_update(self):
        ctx = AgentContext(dataSource="postgresql")
        ctx.lastQuery = QueryState(
            sql="SELECT 1", rowCount=1, executionTimeMs=5, columns=["?column?"]
        )
        # Other fields should remain at defaults
        assert ctx.currentVisualization is None
        assert ctx.activeFilters == {}
        assert ctx.dataSource == "postgresql"

    def test_active_filters_merge(self):
        ctx = AgentContext(activeFilters={"region": "West"})
        # Simulate merging more filters
        ctx.activeFilters["status"] = "on_track"
        assert ctx.activeFilters == {"region": "West", "status": "on_track"}

    def test_invalid_state_rejected(self):
        with pytest.raises(ValidationError):
            # dataShape requires rows (int) and columns (list[str])
            VisualizationState(
                chartType="bar",
                title="Test",
                surfaceId="x",
                sourceQuery="SELECT 1",
                dataShape={"rows": "not_a_number", "columns": 42},  # invalid types
            )
