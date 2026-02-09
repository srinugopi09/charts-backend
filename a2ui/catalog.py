"""A2UI component catalog and color palettes.

Single source of truth for available component types and their visual styles.
"""

# ---------------------------------------------------------------------------
# Catalog identifier (used in createSurface messages)
# ---------------------------------------------------------------------------

CATALOG_ID = "urn:analytics-chatbot:catalog/v1"

# ---------------------------------------------------------------------------
# Valid chart types
# ---------------------------------------------------------------------------

VALID_CHART_TYPES = frozenset({
    "bar",
    "line",
    "pie",
    "doughnut",
    "area",
    "radar",
    "scatter",
    "horizontalBar",
    "stackedBar",
    "stackedArea",
})

# ---------------------------------------------------------------------------
# Valid component types
# ---------------------------------------------------------------------------

COMPONENT_TYPES = frozenset({
    "Graph",
    "KPICard",
    "DataTable",
    "RAGIndicator",
    "InsightCard",
    "CompositeDashboard",
})

# ---------------------------------------------------------------------------
# Color palettes
# ---------------------------------------------------------------------------

COLOR_PALETTES: dict[str, list[str]] = {
    "default": [
        "#4285F4",  # Blue
        "#0F9D58",  # Green
        "#F4B400",  # Yellow
        "#DB4437",  # Red
        "#AB47BC",  # Purple
        "#00ACC1",  # Teal
        "#FF7043",  # Orange
        "#8D6E63",  # Brown
    ],
    "sequential": [
        "#E3F2FD",
        "#BBDEFB",
        "#90CAF9",
        "#64B5F6",
        "#42A5F5",
        "#2196F3",
        "#1E88E5",
        "#1565C0",
    ],
    "diverging": [
        "#D32F2F",
        "#E57373",
        "#FFCDD2",
        "#F5F5F5",
        "#BBDEFB",
        "#64B5F6",
        "#1976D2",
        "#0D47A1",
    ],
    "status": [
        "#0F9D58",  # Green
        "#F4B400",  # Amber
        "#DB4437",  # Red
    ],
    "categorical": [
        "#4285F4",
        "#0F9D58",
        "#F4B400",
        "#DB4437",
        "#AB47BC",
        "#00ACC1",
        "#FF7043",
        "#8D6E63",
        "#78909C",
        "#C0CA33",
        "#26A69A",
        "#EC407A",
    ],
}


def get_palette(name: str = "default", count: int = 8) -> list[str]:
    """Return `count` colors from the named palette, cycling if needed."""
    palette = COLOR_PALETTES.get(name, COLOR_PALETTES["default"])
    if count <= len(palette):
        return palette[:count]
    # Cycle the palette to fill the requested count
    return [palette[i % len(palette)] for i in range(count)]
