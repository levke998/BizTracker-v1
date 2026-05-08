"""Event ticket actual domain entity."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class EventTicketActual:
    """Ticket-system actuals attached to one event."""

    id: uuid.UUID
    event_id: uuid.UUID
    source_name: str | None
    source_reference: str | None
    sold_quantity: Decimal
    gross_revenue: Decimal
    net_revenue: Decimal | None
    vat_amount: Decimal | None
    vat_rate_id: uuid.UUID | None
    platform_fee_gross: Decimal
    reported_at: datetime | None
    notes: str | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class NewEventTicketActual:
    """Mutable ticket actual payload before persistence."""

    event_id: uuid.UUID
    source_name: str | None
    source_reference: str | None
    sold_quantity: Decimal
    gross_revenue: Decimal
    net_revenue: Decimal | None
    vat_amount: Decimal | None
    vat_rate_id: uuid.UUID | None
    platform_fee_gross: Decimal
    reported_at: datetime | None
    notes: str | None
