"""Inventory movement list query."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from app.modules.inventory.domain.entities.inventory_item import InventoryMovement
from app.modules.inventory.domain.repositories.inventory_item_repository import (
    InventoryItemRepository,
)


@dataclass(slots=True)
class ListInventoryMovementsQuery:
    """Return inventory movements with lightweight filters."""

    repository: InventoryItemRepository

    def execute(
        self,
        *,
        business_unit_id: uuid.UUID | None = None,
        inventory_item_id: uuid.UUID | None = None,
        movement_type: str | None = None,
        limit: int = 50,
    ) -> list[InventoryMovement]:
        return self.repository.list_movements(
            business_unit_id=business_unit_id,
            inventory_item_id=inventory_item_id,
            movement_type=movement_type,
            limit=limit,
        )
