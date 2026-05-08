"""VAT rate domain entity."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class VatRate:
    """Represents one VAT rate used by finance and costing calculations."""

    id: uuid.UUID
    code: str
    name: str
    rate_percent: Decimal
    rate_type: str
    nav_code: str | None
    description: str | None
    valid_from: date | None
    valid_to: date | None
    is_active: bool
    created_at: datetime
    updated_at: datetime
