"""Inventory stock level list query."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from app.modules.inventory.domain.entities.inventory_item import InventoryStockLevel
from app.modules.inventory.domain.repositories.inventory_item_repository import (
    InventoryItemRepository,
)


@dataclass(slots=True)
class ListInventoryStockLevelsQuery:
    """Return aggregated actual stock levels with lightweight filters."""

    repository: InventoryItemRepository

    def execute(
        self,
        *,
        business_unit_id: uuid.UUID | None = None,
        inventory_item_id: uuid.UUID | None = None,
        item_type: str | None = None,
        limit: int = 50,
    ) -> list[InventoryStockLevel]:
        return self.repository.list_stock_levels(
            business_unit_id=business_unit_id,
            inventory_item_id=inventory_item_id,
            item_type=item_type,
            limit=limit,
        )
