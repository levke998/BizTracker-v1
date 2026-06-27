"""Event cost line domain entities."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class EventCostLine:
    """One auditable gross cost line attached to a Flow event."""

    id: uuid.UUID
    event_id: uuid.UUID
    category: str
    description: str
    amount_gross: Decimal
    source_type: str
    source_reference: str | None
    incurred_at: datetime | None
    notes: str | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class NewEventCostLine:
    """Draft event cost line before persistence."""

    event_id: uuid.UUID
    category: str
    description: str
    amount_gross: Decimal
    source_type: str
    source_reference: str | None
    incurred_at: datetime | None
    notes: str | None
