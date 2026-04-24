"""Dashboard response schemas."""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class DashboardPeriodResponse(BaseModel):
    """Resolved dashboard period."""

    model_config = ConfigDict(from_attributes=True)

    preset: str
    start_date: date
    end_date: date
    grain: str


class DashboardKpiResponse(BaseModel):
    """KPI tile response."""

    model_config = ConfigDict(from_attributes=True)

    code: str
    label: str
    value: Decimal
    unit: str
    source_layer: str


class DashboardTrendPointResponse(BaseModel):
    """Trend chart point response."""

    model_config = ConfigDict(from_attributes=True)

    period_start: date
    revenue: Decimal
    cost: Decimal
    profit: Decimal


class DashboardBreakdownRowResponse(BaseModel):
    """Category or product breakdown response row."""

    model_config = ConfigDict(from_attributes=True)

    label: str
    revenue: Decimal
    quantity: Decimal
    transaction_count: int
    source_layer: str


class DashboardExpenseRowResponse(BaseModel):
    """Expense breakdown response row."""

    model_config = ConfigDict(from_attributes=True)

    label: str
    amount: Decimal
    transaction_count: int
    source_layer: str


class DashboardProductDetailRowResponse(BaseModel):
    """Product drill-down response row."""

    model_config = ConfigDict(from_attributes=True)

    product_name: str
    category_name: str
    revenue: Decimal
    quantity: Decimal
    transaction_count: int
    source_layer: str


class DashboardExpenseDetailRowResponse(BaseModel):
    """Expense transaction drill-down response row."""

    model_config = ConfigDict(from_attributes=True)

    transaction_id: uuid.UUID
    transaction_type: str
    amount: Decimal
    currency: str
    occurred_at: date
    description: str
    source_type: str
    source_id: uuid.UUID
    source_layer: str


class DashboardResponse(BaseModel):
    """Business dashboard response."""

    model_config = ConfigDict(from_attributes=True)

    scope: str
    business_unit_id: uuid.UUID | None
    business_unit_name: str | None
    period: DashboardPeriodResponse
    kpis: list[DashboardKpiResponse]
    revenue_trend: list[DashboardTrendPointResponse]
    category_breakdown: list[DashboardBreakdownRowResponse]
    top_products: list[DashboardBreakdownRowResponse]
    expense_breakdown: list[DashboardExpenseRowResponse]
    notes: list[str]
