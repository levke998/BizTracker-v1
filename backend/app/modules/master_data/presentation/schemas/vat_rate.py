"""VAT rate response schema."""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

from app.modules.master_data.presentation.schemas.common import MasterDataBaseSchema


class VatRateResponse(MasterDataBaseSchema):
    """Read-only VAT rate response."""

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
