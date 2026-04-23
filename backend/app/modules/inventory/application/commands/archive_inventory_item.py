"""Archive inventory item use case."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from app.modules.inventory.application.commands.update_inventory_item import (
    InventoryItemNotFoundError,
)
from app.modules.inventory.domain.entities.inventory_item import InventoryItem
from app.modules.inventory.domain.repositories.inventory_item_repository import (
    InventoryItemRepository,
)


@dataclass(slots=True)
class ArchiveInventoryItemCommand:
    """Archive one inventory item by marking it inactive."""

    repository: InventoryItemRepository

    def execute(self, *, inventory_item_id: uuid.UUID) -> InventoryItem:
        existing_item = self.repository.get_by_id(inventory_item_id)
        if existing_item is None:
            raise InventoryItemNotFoundError(
                f"Inventory item {inventory_item_id} was not found."
            )

        return self.repository.archive(inventory_item_id)
