"""Builders for individual A2UI component surfaces (v0.9 spec-compliant).

Each builder returns a dict matching the A2UIPayload schema:
  {"a2ui": True, "surfaceId": "...", "messages": [createSurface, updateComponents]}

Components use flat properties (no nested 'properties' dict) with a
'component' discriminator field, per the A2UI v0.9 specification.
"""

import uuid

from a2ui.catalog import CATALOG_ID, VALID_CHART_TYPES, get_palette


def _make_surface_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


def _wrap(surface_id: str, components: list[dict]) -> dict:
    """Wrap components in the spec-compliant A2UI payload."""
    return {
        "a2ui": True,
        "surfaceId": surface_id,
        "messages": [
            {"createSurface": {"surfaceId": surface_id, "catalogId": CATALOG_ID}},
            {"updateComponents": {"surfaceId": surface_id, "components": components}},
        ],
    }


def build_chart_surface(
    chart_type: str,
    title: str,
    labels: list[str],
    datasets: list[dict],
    x_label: str = "",
    y_label: str = "",
    interactive: bool = False,
    color_scheme: str = "default",
) -> dict:
    """Build an A2UI Graph component surface payload."""
    if chart_type not in VALID_CHART_TYPES:
        return {
            "error": f"Invalid chart_type '{chart_type}'. Valid types: {', '.join(sorted(VALID_CHART_TYPES))}"
        }

    # Apply color palette to datasets missing explicit colors
    num_items = max(len(labels), 1)
    palette = get_palette(color_scheme, num_items)

    processed_datasets = []
    for ds in datasets:
        processed = dict(ds)
        if not processed.get("backgroundColor"):
            processed["backgroundColor"] = palette[:len(processed.get("data", []))]
        if not processed.get("borderColor"):
            processed["borderColor"] = processed["backgroundColor"]
        processed_datasets.append(processed)

    surface_id = _make_surface_id("chart")
    root = {
        "id": "root",
        "component": "Graph",
        "graphType": chart_type,
        "title": title,
        "data": {
            "labels": labels,
            "datasets": processed_datasets,
        },
        "xLabel": x_label,
        "yLabel": y_label,
        "interactive": interactive,
        "showLegend": True,
        "colorScheme": color_scheme,
    }
    return _wrap(surface_id, [root])


def build_kpi_surface(
    label: str,
    value: str | int | float,
    unit: str = "",
    trend: str = "",
    trend_value: str = "",
    trend_period: str = "",
    status: str = "",
) -> dict:
    """Build an A2UI KPICard component surface payload."""
    surface_id = _make_surface_id("kpi")
    root: dict = {"id": "root", "component": "KPICard", "label": label, "value": value}
    if unit:
        root["unit"] = unit
    if trend:
        root["trend"] = trend
    if trend_value:
        root["trendValue"] = trend_value
    if trend_period:
        root["trendPeriod"] = trend_period
    if status:
        root["status"] = status

    return _wrap(surface_id, [root])


def build_data_table_surface(
    title: str,
    columns: list[dict],
    rows: list[list],
    sortable: bool = True,
    filterable: bool = True,
    page_size: int = 25,
) -> dict:
    """Build an A2UI DataTable component surface payload."""
    surface_id = _make_surface_id("table")
    root = {
        "id": "root",
        "component": "DataTable",
        "title": title,
        "columns": columns,
        "rows": rows,
        "sortable": sortable,
        "filterable": filterable,
        "pageSize": page_size,
    }
    return _wrap(surface_id, [root])


def build_rag_surface(
    label: str,
    status: str,
    detail: str = "",
    metric: str = "",
    threshold: str = "",
) -> dict:
    """Build an A2UI RAGIndicator component surface payload."""
    surface_id = _make_surface_id("rag")
    root: dict = {"id": "root", "component": "RAGIndicator", "label": label, "status": status}
    if detail:
        root["detail"] = detail
    if metric:
        root["metric"] = metric
    if threshold:
        root["threshold"] = threshold

    return _wrap(surface_id, [root])


def build_insight_surface(
    title: str,
    body: str,
    icon: str = "info",
    priority: str = "medium",
) -> dict:
    """Build an A2UI InsightCard component surface payload."""
    surface_id = _make_surface_id("insight")
    root = {
        "id": "root",
        "component": "InsightCard",
        "title": title,
        "body": body,
        "icon": icon,
        "priority": priority,
    }
    return _wrap(surface_id, [root])
