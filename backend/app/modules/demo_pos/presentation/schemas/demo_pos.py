"""Demo POS API schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class DemoPosBaseSchema(BaseModel):
    """Shared Pydantic configuration."""

    model_config = ConfigDict(from_attributes=True)


class DemoPosCatalogProductResponse(DemoPosBaseSchema):
    """One sellable product available to the demo POS."""

    id: uuid.UUID
    business_unit_id: uuid.UUID
    category_id: uuid.UUID | None
    category_name: str | None
    sales_uom_id: uuid.UUID | None
    sales_uom_code: str | None
    sales_uom_symbol: str | None
    sku: str | None
    name: str
    product_type: str
    sale_price_gross: Decimal
    default_unit_cost: Decimal | None
    currency: str


class DemoPosReceiptLineRequest(BaseModel):
    """One receipt line sent by the demo POS."""

    product_id: uuid.UUID
    quantity: Decimal = Field(gt=0)


class DemoPosReceiptRequest(BaseModel):
    """Receipt payload accepted by the demo POS API."""

    business_unit_id: uuid.UUID
    payment_method: str = Field(default="card", min_length=1, max_length=50)
    receipt_no: str | None = Field(default=None, max_length=100)
    occurred_at: datetime | None = None
    lines: list[DemoPosReceiptLineRequest] = Field(min_length=1)


class DemoPosReceiptLineResponse(DemoPosBaseSchema):
    """One created demo POS receipt line."""

    product_id: uuid.UUID
    product_name: str
    category_name: str | None
    quantity: Decimal
    unit_price_gross: Decimal
    gross_amount: Decimal
    import_row_id: uuid.UUID
    transaction_id: uuid.UUID


class DemoPosReceiptResponse(DemoPosBaseSchema):
    """Created receipt response."""

    business_unit_id: uuid.UUID
    receipt_no: str
    payment_method: str
    occurred_at: datetime
    batch_id: uuid.UUID
    gross_total: Decimal
    transaction_count: int
    lines: tuple[DemoPosReceiptLineResponse, ...]
