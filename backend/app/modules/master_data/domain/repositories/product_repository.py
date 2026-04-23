"""Product repository contract."""

from __future__ import annotations

import uuid
from typing import Protocol

from app.modules.master_data.domain.entities.product import Product


class ProductRepository(Protocol):
    """Defines product read access needed in the MVP."""

    def list_by_business_unit(
        self,
        business_unit_id: uuid.UUID,
        *,
        active_only: bool = True,
    ) -> list[Product]:
        """Return products for a business unit."""
