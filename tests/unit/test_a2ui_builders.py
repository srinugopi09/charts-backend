"""Tests for A2UI builder functions: spec-compliant JSON structure, properties, and edge cases."""

import pytest

from a2ui.catalog import CATALOG_ID, VALID_CHART_TYPES, get_palette
from a2ui.chart_builder import (
    build_chart_surface,
    build_kpi_surface,
    build_data_table_surface,
    build_rag_surface,
    build_insight_surface,
)
from a2ui.dashboard_builder import build_dashboard_surface


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_root(payload: dict) -> dict:
    """Extract the root component from a spec-compliant payload."""
    components = payload["messages"][1]["updateComponents"]["components"]
    return next(c for c in components if c["id"] == "root")


def _get_component(payload: dict, component_id: str) -> dict:
    """Extract a specific component by ID."""
    components = payload["messages"][1]["updateComponents"]["components"]
    return next(c for c in components if c["id"] == component_id)


def _get_all_components(payload: dict) -> list[dict]:
    """Extract all components from a spec-compliant payload."""
    return payload["messages"][1]["updateComponents"]["components"]


def _assert_valid_envelope(payload: dict):
    """Assert that the payload has proper A2UI v0.9 envelope structure."""
    assert payload["a2ui"] is True
    assert "surfaceId" in payload
    assert len(payload["messages"]) == 2
    # First message: createSurface
    cs = payload["messages"][0]["createSurface"]
    assert cs["surfaceId"] == payload["surfaceId"]
    assert cs["catalogId"] == CATALOG_ID
    # Second message: updateComponents
    uc = payload["messages"][1]["updateComponents"]
    assert uc["surfaceId"] == payload["surfaceId"]
    assert len(uc["components"]) > 0
    # Must have a root component
    root_ids = [c["id"] for c in uc["components"] if c["id"] == "root"]
    assert len(root_ids) == 1, "Must have exactly one root component"


SAMPLE_LABELS = ["East", "West", "North", "South"]
SAMPLE_DATASETS = [{"label": "Revenue", "data": [100, 200, 150, 80]}]


# ---------------------------------------------------------------------------
# Graph tests
# ---------------------------------------------------------------------------

class TestGraphBuilder:
    def test_graph_bar_structure(self):
        result = build_chart_surface("bar", "Revenue by Region", SAMPLE_LABELS, SAMPLE_DATASETS)
        _assert_valid_envelope(result)
        root = _get_root(result)
        assert root["component"] == "Graph"
        assert root["graphType"] == "bar"
        assert root["title"] == "Revenue by Region"
        assert len(root["data"]["labels"]) == 4

    def test_graph_line_structure(self):
        result = build_chart_surface("line", "Trend", SAMPLE_LABELS, SAMPLE_DATASETS)
        root = _get_root(result)
        assert root["graphType"] == "line"

    def test_graph_pie_structure(self):
        result = build_chart_surface("pie", "Distribution", SAMPLE_LABELS, SAMPLE_DATASETS)
        root = _get_root(result)
        assert root["graphType"] == "pie"

    @pytest.mark.parametrize("chart_type", sorted(VALID_CHART_TYPES))
    def test_graph_all_types(self, chart_type):
        result = build_chart_surface(chart_type, "Test", ["A", "B"], [{"label": "X", "data": [1, 2]}])
        assert "error" not in result
        _assert_valid_envelope(result)
        root = _get_root(result)
        assert root["component"] == "Graph"
        assert root["graphType"] == chart_type

    def test_graph_color_scheme_default(self):
        result = build_chart_surface("bar", "Test", SAMPLE_LABELS, SAMPLE_DATASETS)
        root = _get_root(result)
        ds = root["data"]["datasets"][0]
        # Should have colors applied from default palette
        assert ds["backgroundColor"] is not None
        assert len(ds["backgroundColor"]) > 0

    def test_graph_color_scheme_custom(self):
        result = build_chart_surface(
            "bar", "Test", SAMPLE_LABELS, SAMPLE_DATASETS, color_scheme="sequential"
        )
        root = _get_root(result)
        ds = root["data"]["datasets"][0]
        seq_palette = get_palette("sequential", 4)
        assert ds["backgroundColor"] == seq_palette

    def test_graph_value_prefix(self):
        result = build_chart_surface(
            "bar", "Revenue", SAMPLE_LABELS, SAMPLE_DATASETS, value_prefix="$"
        )
        root = _get_root(result)
        assert root["valuePrefix"] == "$"
        assert root["valueSuffix"] == ""

    def test_graph_value_suffix(self):
        result = build_chart_surface(
            "line", "Growth Rate", SAMPLE_LABELS, SAMPLE_DATASETS, value_suffix="%"
        )
        root = _get_root(result)
        assert root["valuePrefix"] == ""
        assert root["valueSuffix"] == "%"

    def test_graph_value_prefix_defaults_empty(self):
        result = build_chart_surface("bar", "Count", SAMPLE_LABELS, SAMPLE_DATASETS)
        root = _get_root(result)
        assert root["valuePrefix"] == ""
        assert root["valueSuffix"] == ""


# ---------------------------------------------------------------------------
# KPI Card tests
# ---------------------------------------------------------------------------

class TestKPICardBuilder:
    def test_kpi_card_structure(self):
        result = build_kpi_surface("Total Revenue", "$1.2M")
        _assert_valid_envelope(result)
        root = _get_root(result)
        assert root["component"] == "KPICard"
        assert root["label"] == "Total Revenue"
        assert root["value"] == "$1.2M"

    def test_kpi_card_with_trend(self):
        result = build_kpi_surface(
            "Revenue", 1200000, unit="$", trend="up", trend_value="+12%", trend_period="vs Q3"
        )
        root = _get_root(result)
        assert root["trend"] == "up"
        assert root["trendValue"] == "+12%"
        assert root["trendPeriod"] == "vs Q3"


# ---------------------------------------------------------------------------
# DataTable tests
# ---------------------------------------------------------------------------

class TestDataTableBuilder:
    def test_data_table_structure(self):
        columns = [
            {"key": "name", "label": "Name", "type": "string"},
            {"key": "budget", "label": "Budget", "type": "currency"},
        ]
        rows = [["Project A", 100000], ["Project B", 200000]]
        result = build_data_table_surface("Projects", columns, rows)
        _assert_valid_envelope(result)
        root = _get_root(result)
        assert root["component"] == "DataTable"
        assert root["title"] == "Projects"
        assert len(root["columns"]) == 2
        assert len(root["rows"]) == 2

    def test_data_table_column_types(self):
        columns = [
            {"key": "id", "label": "ID", "type": "number", "align": "right"},
            {"key": "name", "label": "Name", "type": "string"},
            {"key": "date", "label": "Date", "type": "date"},
        ]
        result = build_data_table_surface("Test", columns, [[1, "A", "2025-01-01"]])
        root = _get_root(result)
        for col in root["columns"]:
            assert "key" in col
            assert "label" in col
            assert "type" in col


# ---------------------------------------------------------------------------
# RAG Indicator tests
# ---------------------------------------------------------------------------

class TestRAGIndicatorBuilder:
    def test_rag_indicator_structure(self):
        result = build_rag_surface("System Health", "green", detail="All systems operational")
        _assert_valid_envelope(result)
        root = _get_root(result)
        assert root["component"] == "RAGIndicator"
        assert root["status"] == "green"
        assert root["label"] == "System Health"


# ---------------------------------------------------------------------------
# InsightCard tests
# ---------------------------------------------------------------------------

class TestInsightCardBuilder:
    def test_insight_card_structure(self):
        result = build_insight_surface("Key Finding", "Revenue increased **20%** in Q4")
        _assert_valid_envelope(result)
        root = _get_root(result)
        assert root["component"] == "InsightCard"
        assert "Revenue" in root["body"]


# ---------------------------------------------------------------------------
# Dashboard tests
# ---------------------------------------------------------------------------

class TestDashboardBuilder:
    def test_dashboard_structure(self):
        result = build_dashboard_surface(
            "Overview",
            kpis=[{"label": "Total", "value": 100}],
            charts=[{"chart_type": "bar", "title": "Chart 1", "labels": ["A"], "datasets": [{"label": "X", "data": [1]}]}],
        )
        _assert_valid_envelope(result)
        components = _get_all_components(result)
        root = _get_root(result)
        assert root["component"] == "CompositeDashboard"
        assert root["title"] == "Overview"
        # Children via explicitList
        child_ids = root["children"]["explicitList"]
        assert len(child_ids) == 2  # 1 KPI + 1 chart
        # Children IDs match actual component IDs
        actual_ids = [c["id"] for c in components if c["id"] != "root"]
        assert child_ids == actual_ids

    def test_dashboard_kpis_and_charts(self):
        result = build_dashboard_surface(
            "Health",
            kpis=[
                {"label": "Revenue", "value": "$1M"},
                {"label": "Costs", "value": "$800K"},
            ],
            charts=[
                {"chart_type": "line", "title": "Trend", "labels": ["Jan", "Feb"], "datasets": [{"label": "Rev", "data": [100, 120]}]},
            ],
        )
        components = _get_all_components(result)
        root = _get_root(result)
        child_ids = root["children"]["explicitList"]
        assert len(child_ids) == 3
        # First two children are KPIs, third is a chart
        assert _get_component(result, "kpi-0")["component"] == "KPICard"
        assert _get_component(result, "kpi-1")["component"] == "KPICard"
        assert _get_component(result, "chart-0")["component"] == "Graph"

    def test_dashboard_chart_value_prefix_suffix(self):
        result = build_dashboard_surface(
            "Financial Overview",
            charts=[{
                "chart_type": "bar",
                "title": "Revenue",
                "labels": ["Q1", "Q2"],
                "datasets": [{"label": "Rev", "data": [100, 200]}],
                "value_prefix": "$",
                "value_suffix": "",
            }],
        )
        chart = _get_component(result, "chart-0")
        assert chart["valuePrefix"] == "$"
        assert chart["valueSuffix"] == ""

    def test_dashboard_chart_value_prefix_defaults_empty(self):
        result = build_dashboard_surface(
            "Counts",
            charts=[{
                "chart_type": "bar",
                "title": "Projects",
                "labels": ["A"],
                "datasets": [{"label": "X", "data": [1]}],
            }],
        )
        chart = _get_component(result, "chart-0")
        assert chart["valuePrefix"] == ""
        assert chart["valueSuffix"] == ""

    def test_dashboard_with_insights(self):
        result = build_dashboard_surface(
            "Analysis",
            charts=[{"chart_type": "bar", "title": "Resolution Times", "labels": ["Quality", "Ops"], "datasets": [{"label": "Hours", "data": [19, 38]}]}],
            insights=[{"title": "Key Finding", "body": "Quality dept resolves fastest", "icon": "success", "priority": "high"}],
        )
        _assert_valid_envelope(result)
        root = _get_root(result)
        child_ids = root["children"]["explicitList"]
        assert len(child_ids) == 2  # 1 chart + 1 insight
        # Chart comes before insight
        assert _get_component(result, "chart-0")["component"] == "Graph"
        insight = _get_component(result, "insight-0")
        assert insight["component"] == "InsightCard"
        assert insight["title"] == "Key Finding"
        assert insight["body"] == "Quality dept resolves fastest"
        assert insight["icon"] == "success"
        assert insight["priority"] == "high"

    def test_dashboard_insight_defaults(self):
        result = build_dashboard_surface(
            "Defaults",
            insights=[{"title": "Note", "body": "Some finding"}],
        )
        insight = _get_component(result, "insight-0")
        assert insight["icon"] == "info"
        assert insight["priority"] == "medium"

    def test_node_ids_unique(self):
        result = build_dashboard_surface(
            "Test",
            kpis=[{"label": "A", "value": 1}, {"label": "B", "value": 2}],
            charts=[{"chart_type": "bar", "title": "C", "labels": ["x"], "datasets": [{"label": "Y", "data": [1]}]}],
            tables=[{"title": "T", "columns": [{"key": "k", "label": "K"}], "rows": [[1]]}],
            insights=[{"title": "I", "body": "Finding"}],
        )
        ids = [c["id"] for c in _get_all_components(result)]
        assert len(ids) == len(set(ids)), f"Duplicate IDs found: {ids}"


# ---------------------------------------------------------------------------
# Cross-cutting tests
# ---------------------------------------------------------------------------

class TestCrossCutting:
    def test_a2ui_flag(self):
        """All builders must set a2ui: true and include proper messages."""
        payloads = [
            build_chart_surface("bar", "T", ["A"], [{"label": "X", "data": [1]}]),
            build_kpi_surface("L", 1),
            build_data_table_surface("T", [{"key": "k", "label": "L"}], [[1]]),
            build_rag_surface("L", "green"),
            build_insight_surface("T", "Body"),
            build_dashboard_surface("D"),
        ]
        for p in payloads:
            _assert_valid_envelope(p)

    def test_invalid_chart_type_rejected(self):
        result = build_chart_surface("unknown", "T", ["A"], [{"label": "X", "data": [1]}])
        assert "error" in result

    def test_empty_data_handled(self):
        result = build_chart_surface("bar", "Empty", [], [])
        assert "error" not in result
        root = _get_root(result)
        assert root["data"]["labels"] == []
        assert root["data"]["datasets"] == []

    def test_flat_properties(self):
        """Properties must be flat on the component, not nested under 'properties'."""
        result = build_chart_surface("bar", "Test", ["A"], [{"label": "X", "data": [1]}])
        root = _get_root(result)
        assert "properties" not in root
        assert "graphType" in root
        assert "title" in root

    def test_create_surface_has_catalog_id(self):
        """Every payload must include catalogId in createSurface."""
        result = build_kpi_surface("Test", "100")
        cs = result["messages"][0]["createSurface"]
        assert cs["catalogId"] == CATALOG_ID

    def test_surface_id_consistency(self):
        """surfaceId must be consistent across wrapper and messages."""
        result = build_chart_surface("bar", "T", ["A"], [{"label": "X", "data": [1]}])
        wrapper_id = result["surfaceId"]
        cs_id = result["messages"][0]["createSurface"]["surfaceId"]
        uc_id = result["messages"][1]["updateComponents"]["surfaceId"]
        assert wrapper_id == cs_id == uc_id
