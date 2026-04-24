"""Business dashboard read-model entities."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class DashboardPeriod:
    """Resolved date window used by dashboard calculations."""

    preset: str
    start_date: date
    end_date: date
    grain: str


@dataclass(frozen=True, slots=True)
class DashboardKpi:
    """One high-level business KPI tile."""

    code: str
    label: str
    value: Decimal
    unit: str
    source_layer: str


@dataclass(frozen=True, slots=True)
class DashboardTrendPoint:
    """Time-series point for charting revenue, cost and profit."""

    period_start: date
    revenue: Decimal
    cost: Decimal
    profit: Decimal


@dataclass(frozen=True, slots=True)
class DashboardBreakdownRow:
    """Aggregated row for category or product drill-down."""

    label: str
    revenue: Decimal
    quantity: Decimal
    transaction_count: int
    source_layer: str


@dataclass(frozen=True, slots=True)
class DashboardExpenseRow:
    """Aggregated expense row for cost analysis."""

    label: str
    amount: Decimal
    transaction_count: int
    source_layer: str


@dataclass(frozen=True, slots=True)
class DashboardProductDetailRow:
    """Product drill-down row with optional category context."""

    product_name: str
    category_name: str
    revenue: Decimal
    quantity: Decimal
    transaction_count: int
    source_layer: str


@dataclass(frozen=True, slots=True)
class DashboardExpenseDetailRow:
    """Expense drill-down row backed by financial transactions."""

    transaction_id: uuid.UUID
    transaction_type: str
    amount: Decimal
    currency: str
    occurred_at: date
    description: str
    source_type: str
    source_id: uuid.UUID
    source_layer: str


@dataclass(frozen=True, slots=True)
class DashboardSnapshot:
    """Top-level dashboard payload."""

    scope: str
    business_unit_id: uuid.UUID | None
    business_unit_name: str | None
    period: DashboardPeriod
    kpis: tuple[DashboardKpi, ...]
    revenue_trend: tuple[DashboardTrendPoint, ...]
    category_breakdown: tuple[DashboardBreakdownRow, ...]
    top_products: tuple[DashboardBreakdownRow, ...]
    expense_breakdown: tuple[DashboardExpenseRow, ...]
    notes: tuple[str, ...]
