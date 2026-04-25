"""Finance domain entities."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class FinancialTransaction:
    """Represents one stored finance transaction."""

    id: uuid.UUID
    business_unit_id: uuid.UUID
    direction: str
    transaction_type: str
    amount: Decimal
    currency: str
    occurred_at: datetime
    description: str
    source_type: str
    source_id: uuid.UUID
    dedupe_key: str | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class NewFinancialTransaction:
    """Draft finance transaction before persistence."""

    business_unit_id: uuid.UUID
    direction: str
    transaction_type: str
    amount: Decimal
    currency: str
    occurred_at: datetime
    description: str
    source_type: str
    source_id: uuid.UUID
    dedupe_key: str | None = None
