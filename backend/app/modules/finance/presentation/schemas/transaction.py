"""Finance response schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class FinancialTransactionResponse(BaseModel):
    """Read model for one finance transaction."""

    model_config = ConfigDict(from_attributes=True)

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
