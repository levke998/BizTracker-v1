"""Inventory variance trend query."""

from __future__ import annotations

import uuid

from app.modules.inventory.domain.entities.inventory_item import (
    InventoryVarianceTrendPoint,
)
from app.modules.inventory.domain.repositories.inventory_item_repository import (
    InventoryItemRepository,
)


class ListInventoryVarianceTrendQuery:
    """Return daily correction movement totals."""

    def __init__(self, repository: InventoryItemRepository) -> None:
        self.repository = repository

    def execute(
        self,
        *,
        business_unit_id: uuid.UUID | None = None,
        inventory_item_id: uuid.UUID | None = None,
        days: int = 30,
    ) -> list[InventoryVarianceTrendPoint]:
        return self.repository.list_variance_trend(
            business_unit_id=business_unit_id,
            inventory_item_id=inventory_item_id,
            days=days,
        )
