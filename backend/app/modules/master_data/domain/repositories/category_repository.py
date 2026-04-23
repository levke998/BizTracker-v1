"""Category repository contract."""

from __future__ import annotations

import uuid
from typing import Protocol

from app.modules.master_data.domain.entities.category import Category


class CategoryRepository(Protocol):
    """Defines category read access needed in the MVP."""

    def list_by_business_unit(
        self,
        business_unit_id: uuid.UUID,
        *,
        active_only: bool = True,
    ) -> list[Category]:
        """Return categories for a business unit."""
