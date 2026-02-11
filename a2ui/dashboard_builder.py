"""Builder for A2UI CompositeDashboard surfaces (v0.9 spec-compliant).

A dashboard contains child KPICard, Graph, and DataTable components
referenced by their IDs via the spec's 'children.explicitList' format.
"""

import re

from a2ui.catalog import CATALOG_ID, get_palette


def _sanitize_id(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def build_dashboard_surface(
    title: str,
    kpis: list[dict] | None = None,
    charts: list[dict] | None = None,
    tables: list[dict] | None = None,
    layout: str = "auto",
) -> dict:
    """Build an A2UI CompositeDashboard surface payload.

    Returns a spec-compliant A2UI payload with createSurface + updateComponents
    messages. The root CompositeDashboard uses children.explicitList to
    reference child component IDs.
    """
    kpis = kpis or []
    charts = charts or []
    tables = tables or []

    components = []
    child_ids = []

    # KPI cards
    for i, kpi in enumerate(kpis):
        comp_id = f"kpi-{i}"
        child_ids.append(comp_id)
        comp: dict = {
            "id": comp_id,
            "component": "KPICard",
            "label": kpi.get("label", ""),
            "value": kpi.get("value", ""),
        }
        for key in ("unit", "trend", "trendValue", "trend_value", "trendPeriod", "trend_period", "status"):
            # Normalize snake_case to camelCase
            camel = key.replace("_v", "V").replace("_p", "P")
            val = kpi.get(key) or kpi.get(camel)
            if val:
                comp[camel] = val
        components.append(comp)

    # Charts
    for i, chart in enumerate(charts):
        comp_id = f"chart-{i}"
        child_ids.append(comp_id)
        chart_type = chart.get("chart_type", "bar")
        labels = chart.get("labels", [])
        datasets = chart.get("datasets", [])

        # Apply default colors
        palette = get_palette(chart.get("color_scheme", "default"), max(len(labels), 1))
        processed_datasets = []
        for ds in datasets:
            processed = dict(ds)
            if not processed.get("backgroundColor"):
                processed["backgroundColor"] = palette[:len(processed.get("data", []))]
            if not processed.get("borderColor"):
                processed["borderColor"] = processed["backgroundColor"]
            processed_datasets.append(processed)

        components.append({
            "id": comp_id,
            "component": "Graph",
            "graphType": chart_type,
            "title": chart.get("title", ""),
            "data": {"labels": labels, "datasets": processed_datasets},
            "xLabel": chart.get("x_label", ""),
            "yLabel": chart.get("y_label", ""),
            "interactive": chart.get("interactive", False),
            "showLegend": True,
            "colorScheme": chart.get("color_scheme", "default"),
            "valuePrefix": chart.get("value_prefix", ""),
            "valueSuffix": chart.get("value_suffix", ""),
        })

    # Tables
    for i, table in enumerate(tables):
        comp_id = f"table-{i}"
        child_ids.append(comp_id)
        components.append({
            "id": comp_id,
            "component": "DataTable",
            "title": table.get("title", ""),
            "columns": table.get("columns", []),
            "rows": table.get("rows", []),
            "sortable": table.get("sortable", True),
            "filterable": table.get("filterable", True),
            "pageSize": table.get("page_size", 25),
        })

    # Dashboard root component (must be first, with id "root")
    surface_id = f"dashboard-{_sanitize_id(title)}"
    root = {
        "id": "root",
        "component": "CompositeDashboard",
        "title": title,
        "layout": layout,
        "children": {"explicitList": child_ids},
    }

    return {
        "a2ui": True,
        "surfaceId": surface_id,
        "messages": [
            {"createSurface": {"surfaceId": surface_id, "catalogId": CATALOG_ID}},
            {"updateComponents": {
                "surfaceId": surface_id,
                "components": [root] + components,
            }},
        ],
    }
