"""Procurement purchase invoice domain entities."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class PurchaseInvoiceLine:
    """Represents one persisted purchase invoice line."""

    id: uuid.UUID
    inventory_item_id: uuid.UUID | None
    description: str
    quantity: Decimal
    uom_id: uuid.UUID
    unit_net_amount: Decimal
    line_net_amount: Decimal


@dataclass(frozen=True, slots=True)
class NewPurchaseInvoiceLine:
    """Draft purchase invoice line before persistence."""

    inventory_item_id: uuid.UUID | None
    description: str
    quantity: Decimal
    uom_id: uuid.UUID
    unit_net_amount: Decimal
    line_net_amount: Decimal


@dataclass(frozen=True, slots=True)
class PurchaseInvoice:
    """Represents one persisted purchase invoice with its lines."""

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
    lines: tuple[PurchaseInvoiceLine, ...]


@dataclass(frozen=True, slots=True)
class NewPurchaseInvoice:
    """Draft purchase invoice before persistence."""

    business_unit_id: uuid.UUID
    supplier_id: uuid.UUID
    invoice_number: str
    invoice_date: date
    currency: str
    gross_total: Decimal
    notes: str | None
    lines: tuple[NewPurchaseInvoiceLine, ...]
