"""A2UI generation tools for the analytics orchestrator agent.

These are plain Python functions that ADK auto-wraps as FunctionTool.
Each delegates to a builder and returns an A2UI v0.9 spec-compliant payload.

The optional `tool_context` parameter is auto-injected by ADK when the
agent calls these tools, enabling shared state updates.

Note: Complex nested parameters (datasets, columns, rows, kpis, charts,
tables) are typed as `str` (JSON strings) because the Gemini function
calling API does not support `list[dict]` schemas. The functions parse
the JSON internally.
"""

import json

from a2ui.chart_builder import (
    build_chart_surface,
    build_kpi_surface,
    build_data_table_surface,
    build_rag_surface,
    build_insight_surface,
)
from a2ui.dashboard_builder import build_dashboard_surface


def _parse_json_param(value, default=None):
    """Parse a JSON string parameter, passing through if already parsed."""
    if value is None:
        return default
    if isinstance(value, (list, dict)):
        return value
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return default


def _update_viz_state(tool_context, chart_type: str, title: str, surface_id: str, labels: list[str] | None = None):
    """Update currentVisualization in shared state if tool_context is available."""
    if tool_context is None:
        return
    last_query = tool_context.state.get("lastQuery", {})
    tool_context.state["currentVisualization"] = {
        "chartType": chart_type,
        "title": title,
        "surfaceId": surface_id,
        "sourceQuery": last_query.get("sql", ""),
        "dataShape": {
            "rows": last_query.get("rowCount", 0),
            "columns": labels or last_query.get("columns", []),
        },
        "interactive": True,
    }


def generate_chart(
    chart_type: str,
    title: str,
    labels: list[str],
    datasets: str,
    x_label: str = "",
    y_label: str = "",
    interactive: bool = False,
    color_scheme: str = "default",
    value_prefix: str = "",
    value_suffix: str = "",
    tool_context=None,
) -> dict:
    """Generates an A2UI Graph component for the frontend to render.

    Use this tool to create visualizations like bar charts, line charts, pie charts, etc.

    Args:
        chart_type: One of: bar, line, pie, doughnut, area, radar, scatter,
                    horizontalBar, stackedBar, stackedArea.
        title: Chart title (descriptive but concise).
        labels: X-axis or segment labels.
        datasets: JSON string — array of dataset objects, each with 'label' (str) and 'data' (list of numbers).
                  Example: '[{"label": "Revenue", "data": [100, 200, 300]}]'
        x_label: X-axis label.
        y_label: Y-axis label.
        interactive: Enable drill-down interactions (default False).
        color_scheme: Named palette — "default", "sequential", "diverging", "status", "categorical".
        value_prefix: Symbol prepended to numeric values on axes/tooltips (e.g., "$" for currency). Leave empty for plain numbers.
        value_suffix: Symbol appended to numeric values on axes/tooltips (e.g., "%" for percentages). Leave empty for plain numbers.
        tool_context: ADK ToolContext (auto-injected). Used to update shared state.

    Returns:
        A2UI surface payload with a Graph component.
    """
    datasets_parsed = _parse_json_param(datasets, [])
    payload = build_chart_surface(
        chart_type=chart_type,
        title=title,
        labels=labels,
        datasets=datasets_parsed,
        x_label=x_label,
        y_label=y_label,
        interactive=interactive,
        color_scheme=color_scheme,
        value_prefix=value_prefix,
        value_suffix=value_suffix,
    )
    if "error" not in payload:
        _update_viz_state(tool_context, chart_type, title, payload["surfaceId"], labels)
    return payload


def generate_kpi_card(
    label: str,
    value: str,
    unit: str = "",
    trend: str = "",
    trend_value: str = "",
    trend_period: str = "",
    status: str = "",
    tool_context=None,
) -> dict:
    """Generates an A2UI KPICard component showing a single metric value.

    Use this for single aggregate values like total revenue, project count, etc.

    Args:
        label: Metric name (e.g., "Total Revenue").
        value: Metric value as a string (e.g., "$1.2M", "30", "87%").
        unit: Unit label (e.g., "$", "%", "projects").
        trend: Direction — "up", "down", or "flat".
        trend_value: Delta value (e.g., "+12%").
        trend_period: Comparison period (e.g., "vs Q3 2025").
        status: Health status — "good", "warning", or "critical".
        tool_context: ADK ToolContext (auto-injected). Used to update shared state.

    Returns:
        A2UI surface payload with a KPICard component.
    """
    payload = build_kpi_surface(
        label=label,
        value=value,
        unit=unit,
        trend=trend,
        trend_value=trend_value,
        trend_period=trend_period,
        status=status,
    )
    _update_viz_state(tool_context, "kpi", label, payload["surfaceId"])
    return payload


def generate_data_table(
    title: str,
    columns: str,
    rows: str,
    sortable: bool = True,
    filterable: bool = True,
    page_size: int = 25,
    tool_context=None,
) -> dict:
    """Generates an A2UI DataTable component for displaying tabular data.

    Use this when the user asks to list or show detailed records.

    Args:
        title: Table title.
        columns: JSON string — array of column definitions, each with 'key', 'label', and 'type'
                 (type is one of: "string", "number", "date", "currency").
                 Example: '[{"key": "name", "label": "Name", "type": "string"}]'
        rows: JSON string — array of row data arrays (each row is a list of values matching columns).
              Example: '[["Project Alpha", 100000], ["Project Beta", 200000]]'
        sortable: Enable column sorting (default True).
        filterable: Enable column filtering (default True).
        page_size: Number of rows per page (default 25).
        tool_context: ADK ToolContext (auto-injected). Used to update shared state.

    Returns:
        A2UI surface payload with a DataTable component.
    """
    columns_parsed = _parse_json_param(columns, [])
    rows_parsed = _parse_json_param(rows, [])
    payload = build_data_table_surface(
        title=title,
        columns=columns_parsed,
        rows=rows_parsed,
        sortable=sortable,
        filterable=filterable,
        page_size=page_size,
    )
    col_keys = [c.get("key", c.get("label", "")) for c in columns_parsed]
    _update_viz_state(tool_context, "dataTable", title, payload["surfaceId"], col_keys)
    return payload


def generate_dashboard(
    title: str,
    kpis: str = "[]",
    charts: str = "[]",
    tables: str = "[]",
    insights: str = "[]",
    layout: str = "auto",
    tool_context=None,
) -> dict:
    """Generates an A2UI CompositeDashboard with multiple child components.

    Use this when the user asks for an overview, summary, or dashboard with
    multiple metrics and charts together.

    Args:
        title: Dashboard title.
        kpis: JSON string — array of KPI definitions (each with 'label', 'value', optional 'unit', 'trend').
              Example: '[{"label": "Total Revenue", "value": "$1.2M"}]'
        charts: JSON string — array of chart definitions (each with 'chart_type', 'title', 'labels', 'datasets').
                Example: '[{"chart_type": "bar", "title": "Revenue by Region", "labels": ["East","West"], "datasets": [{"label": "Revenue", "data": [100,200]}]}]'
        tables: JSON string — array of table definitions (each with 'title', 'columns', 'rows').
        insights: JSON string — array of insight definitions (each with 'title', 'body', optional 'icon', 'priority').
                  Example: '[{"title": "Key Finding", "body": "Revenue grew 20% in Q4", "priority": "high"}]'
        layout: Layout mode — "auto", "2-column", "3-column", "1-top-2-bottom".
        tool_context: ADK ToolContext (auto-injected). Used to update shared state.

    Returns:
        A2UI surface payload with a CompositeDashboard root and child components.
    """
    payload = build_dashboard_surface(
        title=title,
        kpis=_parse_json_param(kpis, []),
        charts=_parse_json_param(charts, []),
        tables=_parse_json_param(tables, []),
        insights=_parse_json_param(insights, []),
        layout=layout,
    )
    _update_viz_state(tool_context, "dashboard", title, payload["surfaceId"])
    return payload


def generate_rag_indicator(
    label: str,
    status: str,
    detail: str = "",
    metric: str = "",
    threshold: str = "",
    tool_context=None,
) -> dict:
    """Generates an A2UI RAGIndicator component showing Red/Amber/Green status.

    Use this for status checks, health indicators, or SLA compliance.

    Args:
        label: What this status is for (e.g., "Build Pipeline Health").
        status: One of "red", "amber", or "green".
        detail: Explanation text.
        metric: Underlying metric value.
        threshold: What threshold triggered this status.
        tool_context: ADK ToolContext (auto-injected). Used to update shared state.

    Returns:
        A2UI surface payload with a RAGIndicator component.
    """
    payload = build_rag_surface(
        label=label,
        status=status,
        detail=detail,
        metric=metric,
        threshold=threshold,
    )
    _update_viz_state(tool_context, "rag", label, payload["surfaceId"])
    return payload


def generate_insight_card(
    title: str,
    body: str,
    icon: str = "info",
    priority: str = "medium",
    tool_context=None,
) -> dict:
    """Generates an A2UI InsightCard component for highlighting key findings.

    Use this when you discover a notable pattern, outlier, or trend in the data.

    Args:
        title: Insight title (e.g., "Budget Overrun Detected").
        body: Insight text (markdown supported).
        icon: One of "info", "warning", "success", "tip".
        priority: One of "high", "medium", "low".
        tool_context: ADK ToolContext (auto-injected). Used to update shared state.

    Returns:
        A2UI surface payload with an InsightCard component.
    """
    payload = build_insight_surface(
        title=title,
        body=body,
        icon=icon,
        priority=priority,
    )
    _update_viz_state(tool_context, "insight", title, payload["surfaceId"])
    return payload
