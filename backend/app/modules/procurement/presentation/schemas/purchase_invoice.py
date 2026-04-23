"""Purchase invoice request and response schemas."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class PurchaseInvoiceLineCreateRequest(BaseModel):
    """Create request for one purchase invoice line."""

    inventory_item_id: uuid.UUID | None = None
    description: str = Field(min_length=1, max_length=255)
    quantity: Decimal = Field(gt=0)
    uom_id: uuid.UUID
    unit_net_amount: Decimal = Field(gt=0)
    line_net_amount: Decimal = Field(gt=0)


class PurchaseInvoiceCreateRequest(BaseModel):
    """Create request for one purchase invoice."""

    business_unit_id: uuid.UUID
    supplier_id: uuid.UUID
    invoice_number: str = Field(min_length=1, max_length=120)
    invoice_date: date
    currency: str = Field(default="HUF", min_length=3, max_length=3)
    gross_total: Decimal = Field(gt=0)
    notes: str | None = Field(default=None, max_length=2000)
    lines: list[PurchaseInvoiceLineCreateRequest] = Field(min_length=1)


class PurchaseInvoiceLineResponse(BaseModel):
    """Read model for one purchase invoice line."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    inventory_item_id: uuid.UUID | None
    description: str
    quantity: Decimal
    uom_id: uuid.UUID
    unit_net_amount: Decimal
    line_net_amount: Decimal


class PurchaseInvoiceResponse(BaseModel):
    """Read model for one purchase invoice."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    business_unit_id: uuid.UUID
    supplier_id: uuid.UUID
    supplier_name: str
    invoice_number: str
    invoice_date: date
    currency: str
    gross_total: Decimal
    notes: str | None
    created_at: datetime
    updated_at: datetime
    lines: list[PurchaseInvoiceLineResponse]
