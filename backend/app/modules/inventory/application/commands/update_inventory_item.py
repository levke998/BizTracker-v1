"""Update inventory item use case."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from app.modules.inventory.application.commands.create_inventory_item import (
    InventoryItemAlreadyExistsError,
    InventoryUnitOfMeasureNotFoundError,
)
from app.modules.inventory.domain.entities.inventory_item import InventoryItem
from app.modules.inventory.domain.repositories.inventory_item_repository import (
    InventoryItemRepository,
)


class InventoryItemNotFoundError(Exception):
    """Raised when the target inventory item does not exist."""


@dataclass(slots=True)
class UpdateInventoryItemCommand:
    """Update one inventory item with minimal validation."""

    repository: InventoryItemRepository

    def execute(
        self,
        *,
        inventory_item_id: uuid.UUID,
        name: str,
        item_type: str,
        uom_id: uuid.UUID,
        track_stock: bool,
        is_active: bool,
    ) -> InventoryItem:
        existing_item = self.repository.get_by_id(inventory_item_id)
        if existing_item is None:
            raise InventoryItemNotFoundError(
                f"Inventory item {inventory_item_id} was not found."
            )

        normalized_name = name.strip()
        normalized_item_type = item_type.strip()

        if not self.repository.unit_of_measure_exists(uom_id):
            raise InventoryUnitOfMeasureNotFoundError(
                f"Unit of measure {uom_id} was not found."
            )
        if self.repository.exists_by_name(
            business_unit_id=existing_item.business_unit_id,
            name=normalized_name,
            exclude_inventory_item_id=inventory_item_id,
        ):
            raise InventoryItemAlreadyExistsError(
                "An inventory item with the same name already exists in this business unit."
            )

        return self.repository.update(
            inventory_item_id=inventory_item_id,
            name=normalized_name,
            item_type=normalized_item_type,
            uom_id=uom_id,
            track_stock=track_stock,
            is_active=is_active,
        )
