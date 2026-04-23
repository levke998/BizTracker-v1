"""Inventory item list query."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from app.modules.inventory.domain.entities.inventory_item import InventoryItem
from app.modules.inventory.domain.repositories.inventory_item_repository import (
    InventoryItemRepository,
)


@dataclass(slots=True)
class ListInventoryItemsQuery:
    """Return inventory items with lightweight filters."""

    repository: InventoryItemRepository

    def execute(
        self,
        *,
        business_unit_id: uuid.UUID | None = None,
        item_type: str | None = None,
        limit: int = 50,
    ) -> list[InventoryItem]:
        return self.repository.list_many(
            business_unit_id=business_unit_id,
            item_type=item_type,
            limit=limit,
        )
