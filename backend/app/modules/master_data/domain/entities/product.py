"""Product domain entity."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class Product:
    """Represents a sellable or business-tracked product."""

    id: uuid.UUID
    business_unit_id: uuid.UUID
    category_id: uuid.UUID | None
    sku: str | None
    name: str
    product_type: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
