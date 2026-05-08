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
    vat_rate_id: uuid.UUID | None = None
    vat_amount: Decimal | None = Field(default=None, ge=0)
    line_gross_amount: Decimal | None = Field(default=None, ge=0)


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
    vat_rate_id: uuid.UUID | None
    vat_amount: Decimal | None
    line_gross_amount: Decimal | None


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
    is_posted: bool
    posted_to_finance: bool
    posted_inventory_movement_count: int
    created_at: datetime
    updated_at: datetime
    lines: list[PurchaseInvoiceLineResponse]


class PurchaseInvoicePostingResponse(BaseModel):
    """Summary response for posting a purchase invoice to downstream actuals."""

    model_config = ConfigDict(from_attributes=True)

    purchase_invoice_id: uuid.UUID
    created_financial_transactions: int
    created_inventory_movements: int
    updated_inventory_item_costs: int
    finance_source_type: str
    inventory_source_type: str


class PurchaseInvoicePdfDraftResponse(BaseModel):
    """Read model for one uploaded PDF invoice draft."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    business_unit_id: uuid.UUID
    supplier_id: uuid.UUID | None
    original_name: str
    stored_path: str
    mime_type: str | None
    size_bytes: int
    status: str
    extraction_status: str
    raw_extraction: dict | None
    review_payload: dict | None
    notes: str | None
    created_at: datetime
    updated_at: datetime


class PurchaseInvoicePdfReviewLineRequest(BaseModel):
    """Review payload for one PDF invoice line."""

    description: str = Field(min_length=1, max_length=255)
    supplier_product_name: str | None = Field(default=None, max_length=255)
    inventory_item_id: uuid.UUID | None = None
    quantity: Decimal | None = Field(default=None, gt=0)
    uom_id: uuid.UUID | None = None
    vat_rate_id: uuid.UUID | None = None
    unit_net_amount: Decimal | None = Field(default=None, ge=0)
    line_net_amount: Decimal | None = Field(default=None, ge=0)
    vat_amount: Decimal | None = Field(default=None, ge=0)
    line_gross_amount: Decimal | None = Field(default=None, ge=0)
    notes: str | None = Field(default=None, max_length=1000)


class PurchaseInvoicePdfReviewRequest(BaseModel):
    """Reviewed PDF invoice header and lines."""

    supplier_id: uuid.UUID | None = None
    invoice_number: str | None = Field(default=None, max_length=120)
    invoice_date: date | None = None
    currency: str = Field(default="HUF", min_length=3, max_length=3)
    gross_total: Decimal | None = Field(default=None, ge=0)
    notes: str | None = Field(default=None, max_length=2000)
    lines: list[PurchaseInvoicePdfReviewLineRequest] = Field(default_factory=list)


class SupplierItemAliasResponse(BaseModel):
    """Read model for one supplier item alias mapping row."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    business_unit_id: uuid.UUID
    supplier_id: uuid.UUID
    inventory_item_id: uuid.UUID | None
    source_item_name: str
    source_item_key: str
    internal_display_name: str | None
    status: str
    mapping_confidence: str
    occurrence_count: int
    first_seen_at: datetime
    last_seen_at: datetime
    notes: str | None
    created_at: datetime
    updated_at: datetime


class SupplierItemAliasMappingRequest(BaseModel):
    """Approve one supplier item alias against an internal inventory item."""

    inventory_item_id: uuid.UUID
    internal_display_name: str | None = Field(default=None, max_length=255)
    notes: str | None = Field(default=None, max_length=1000)
