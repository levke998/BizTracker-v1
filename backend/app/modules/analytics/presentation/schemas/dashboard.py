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
    estimated_cogs: Decimal
    margin_profit: Decimal


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


class DashboardPosSourceRowResponse(BaseModel):
    """Source POS import row behind a product drill-down."""

    model_config = ConfigDict(from_attributes=True)

    row_id: uuid.UUID
    row_number: int
    date: date | None
    receipt_no: str | None
    category_name: str
    product_name: str
    quantity: Decimal
    gross_amount: Decimal
    payment_method: str | None
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


class DashboardExpenseSourceLineResponse(BaseModel):
    """Line-level source detail for an expense transaction."""

    model_config = ConfigDict(from_attributes=True)

    line_id: uuid.UUID
    inventory_item_id: uuid.UUID | None
    description: str
    quantity: Decimal
    uom_id: uuid.UUID
    unit_net_amount: Decimal
    line_net_amount: Decimal


class DashboardExpenseSourceResponse(BaseModel):
    """Source record behind one expense transaction."""

    model_config = ConfigDict(from_attributes=True)

    transaction_id: uuid.UUID
    transaction_type: str
    amount: Decimal
    currency: str
    occurred_at: date
    source_type: str
    source_id: uuid.UUID
    supplier_id: uuid.UUID | None
    supplier_name: str | None
    invoice_number: str | None
    invoice_date: date | None
    gross_total: Decimal | None
    notes: str | None
    lines: list[DashboardExpenseSourceLineResponse]


class DashboardBasketPairRowResponse(BaseModel):
    """Frequently co-purchased product pair response row."""

    model_config = ConfigDict(from_attributes=True)

    product_a: str
    product_b: str
    basket_count: int
    total_gross_amount: Decimal
    source_layer: str


class DashboardBasketReceiptLineResponse(BaseModel):
    """One POS source row inside a receipt basket."""

    model_config = ConfigDict(from_attributes=True)

    row_id: uuid.UUID
    row_number: int
    product_name: str
    category_name: str
    quantity: Decimal
    gross_amount: Decimal
    payment_method: str | None


class DashboardBasketReceiptResponse(BaseModel):
    """Source receipt basket for one product-pair drill-down."""

    model_config = ConfigDict(from_attributes=True)

    receipt_no: str
    date: date | None
    gross_amount: Decimal
    quantity: Decimal
    lines: list[DashboardBasketReceiptLineResponse]
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
