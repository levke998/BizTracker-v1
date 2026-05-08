"""Product response schema."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from app.modules.master_data.presentation.schemas.common import MasterDataBaseSchema


class ProductResponse(MasterDataBaseSchema):
    """Read-only product response."""

    id: uuid.UUID
    business_unit_id: uuid.UUID
    category_id: uuid.UUID | None
    sales_uom_id: uuid.UUID | None
    default_vat_rate_id: uuid.UUID | None
    sku: str | None
    name: str
    product_type: str
    sale_price_gross: Decimal | None
    sale_price_last_seen_at: datetime | None
    sale_price_source: str | None
    default_unit_cost: Decimal | None
    currency: str
    is_active: bool
