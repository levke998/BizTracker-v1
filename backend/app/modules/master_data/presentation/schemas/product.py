"""Product response schema."""

from __future__ import annotations

import uuid
from decimal import Decimal

from app.modules.master_data.presentation.schemas.common import MasterDataBaseSchema


class ProductResponse(MasterDataBaseSchema):
    """Read-only product response."""

    id: uuid.UUID
    business_unit_id: uuid.UUID
    category_id: uuid.UUID | None
    sales_uom_id: uuid.UUID | None
    sku: str | None
    name: str
    product_type: str
    sale_price_gross: Decimal | None
    default_unit_cost: Decimal | None
    currency: str
    is_active: bool
