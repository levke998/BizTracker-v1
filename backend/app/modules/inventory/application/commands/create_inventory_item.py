"""Create inventory item use case."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from app.modules.inventory.domain.entities.inventory_item import (
    InventoryItem,
    NewInventoryItem,
)
from app.modules.inventory.domain.repositories.inventory_item_repository import (
    InventoryItemRepository,
)


class InventoryBusinessUnitNotFoundError(Exception):
    """Raised when the selected business unit does not exist."""


class InventoryUnitOfMeasureNotFoundError(Exception):
    """Raised when the selected unit of measure does not exist."""


class InventoryItemAlreadyExistsError(Exception):
    """Raised when an item name already exists in the same business unit."""


@dataclass(slots=True)
class CreateInventoryItemCommand:
    """Create a new inventory item with minimal validation."""

    repository: InventoryItemRepository

    def execute(
        self,
        *,
        business_unit_id: uuid.UUID,
        name: str,
        item_type: str,
        uom_id: uuid.UUID,
        track_stock: bool,
        is_active: bool = True,
    ) -> InventoryItem:
        normalized_name = name.strip()

        if not self.repository.business_unit_exists(business_unit_id):
            raise InventoryBusinessUnitNotFoundError(
                f"Business unit {business_unit_id} was not found."
            )
        if not self.repository.unit_of_measure_exists(uom_id):
            raise InventoryUnitOfMeasureNotFoundError(
                f"Unit of measure {uom_id} was not found."
            )
        if self.repository.exists_by_name(
            business_unit_id=business_unit_id,
            name=normalized_name,
        ):
            raise InventoryItemAlreadyExistsError(
                "An inventory item with the same name already exists in this business unit."
            )

        return self.repository.create(
            NewInventoryItem(
                business_unit_id=business_unit_id,
                name=normalized_name,
                item_type=item_type.strip(),
                uom_id=uom_id,
                track_stock=track_stock,
                is_active=is_active,
            )
        )
