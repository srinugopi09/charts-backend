"""A2UI v0.9 spec-compliant schema definitions.

Defines Pydantic models for A2UI messages (createSurface, updateComponents)
and the AG-UI transport wrapper. Component types (Graph, KPICard, etc.) are
part of a custom catalog for the analytics chatbot.

Ref: https://a2ui.org/specification/v0.9-a2ui/
"""

from typing import Any

from pydantic import BaseModel


# ---------------------------------------------------------------------------
# A2UI v0.9 message models
# ---------------------------------------------------------------------------

class A2UIComponent(BaseModel):
    """A single A2UI component with flat properties (no nested 'properties' dict).

    Per the spec, the 'component' field is the type discriminator, and all
    other properties sit directly on the object.
    """
    id: str
    component: str  # "Graph", "KPICard", "DataTable", "RAGIndicator", "InsightCard", "CompositeDashboard"
    model_config = {"extra": "allow"}


class CreateSurfaceMessage(BaseModel):
    """A2UI createSurface message — initializes a surface."""
    surfaceId: str
    catalogId: str


class UpdateComponentsMessage(BaseModel):
    """A2UI updateComponents message — adds/updates components on a surface."""
    surfaceId: str
    components: list[A2UIComponent]


class A2UIPayload(BaseModel):
    """AG-UI transport wrapper for spec-compliant A2UI messages.

    The 'a2ui' flag lets the frontend identify this as an A2UI payload
    within AG-UI tool results. The 'messages' array contains spec-compliant
    A2UI messages (createSurface + updateComponents).
    """
    a2ui: bool = True
    surfaceId: str
    messages: list[dict[str, Any]]


# ---------------------------------------------------------------------------
# Typed property models (for builder input validation)
# ---------------------------------------------------------------------------

class DatasetDef(BaseModel):
    label: str
    data: list[float | int | None]
    backgroundColor: list[str] | str | None = None
    borderColor: list[str] | str | None = None


class GraphData(BaseModel):
    labels: list[str]
    datasets: list[DatasetDef]


class GraphProperties(BaseModel):
    graphType: str
    title: str
    data: GraphData
    xLabel: str = ""
    yLabel: str = ""
    interactive: bool = True
    showLegend: bool = True
    colorScheme: str = "default"
    valuePrefix: str = ""
    valueSuffix: str = ""


class KPICardProperties(BaseModel):
    label: str
    value: str | int | float
    unit: str = ""
    trend: str = ""  # "up", "down", "flat"
    trendValue: str = ""
    trendPeriod: str = ""
    status: str = ""  # "good", "warning", "critical"


class ColumnDef(BaseModel):
    key: str
    label: str
    type: str = "string"  # "string", "number", "date", "currency"
    align: str = "left"


class DataTableProperties(BaseModel):
    title: str
    columns: list[ColumnDef]
    rows: list[list[Any]]
    sortable: bool = True
    filterable: bool = True
    pageSize: int = 25


class RAGIndicatorProperties(BaseModel):
    label: str
    status: str  # "red", "amber", "green"
    detail: str = ""
    metric: str = ""
    threshold: str = ""


class InsightCardProperties(BaseModel):
    title: str
    body: str
    icon: str = "info"  # "info", "warning", "success", "tip"
    priority: str = "medium"  # "high", "medium", "low"


class CompositeDashboardProperties(BaseModel):
    title: str
    layout: str = "auto"  # "auto", "2-column", "3-column", "1-top-2-bottom"
