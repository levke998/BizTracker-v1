"""Application command for creating inventory movement log entries."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

from app.modules.inventory.domain.entities.inventory_item import (
    InventoryMovement,
    NewInventoryMovement,
)
from app.modules.inventory.domain.repositories.inventory_item_repository import (
    InventoryItemRepository,
)

PURCHASE_MOVEMENT_TYPE = "purchase"


class InventoryMovementBusinessUnitNotFoundError(ValueError):
    """Raised when the business unit does not exist."""


class InventoryMovementInventoryItemNotFoundError(ValueError):
    """Raised when the inventory item does not exist."""


class InventoryMovementUnitOfMeasureNotFoundError(ValueError):
    """Raised when the unit of measure does not exist."""


class InventoryMovementBusinessUnitMismatchError(ValueError):
    """Raised when the inventory item does not belong to the given business unit."""


class InventoryMovementUnitOfMeasureMismatchError(ValueError):
    """Raised when the movement UOM does not match the item UOM."""


class InventoryMovementUnitCostRequiredError(ValueError):
    """Raised when purchase movement misses its unit cost."""


@dataclass(slots=True)
class CreateInventoryMovementCommand:
    """Create inventory movement log entries with minimal validation."""

    repository: InventoryItemRepository

    def execute(
        self,
        *,
        business_unit_id: uuid.UUID,
        inventory_item_id: uuid.UUID,
        movement_type: str,
        quantity: Decimal,
        uom_id: uuid.UUID,
        unit_cost: Decimal | None = None,
        occurred_at: datetime | None = None,
        note: str | None = None,
        source_type: str | None = None,
        source_id: uuid.UUID | None = None,
    ) -> InventoryMovement:
        """Validate references and persist one movement log entry."""

        if not self.repository.business_unit_exists(business_unit_id):
            raise InventoryMovementBusinessUnitNotFoundError(
                f"Business unit '{business_unit_id}' was not found."
            )

        inventory_item = self.repository.get_by_id(inventory_item_id)
        if inventory_item is None:
            raise InventoryMovementInventoryItemNotFoundError(
                f"Inventory item '{inventory_item_id}' was not found."
            )

        if not self.repository.unit_of_measure_exists(uom_id):
            raise InventoryMovementUnitOfMeasureNotFoundError(
                f"Unit of measure '{uom_id}' was not found."
            )

        if inventory_item.business_unit_id != business_unit_id:
            raise InventoryMovementBusinessUnitMismatchError(
                "Inventory item does not belong to the given business unit."
            )

        if inventory_item.uom_id != uom_id:
            raise InventoryMovementUnitOfMeasureMismatchError(
                "Movement unit of measure must match the inventory item unit of measure."
            )

        if movement_type == PURCHASE_MOVEMENT_TYPE and unit_cost is None:
            raise InventoryMovementUnitCostRequiredError(
                "Purchase movements require a unit_cost value."
            )

        movement = NewInventoryMovement(
            business_unit_id=business_unit_id,
            inventory_item_id=inventory_item_id,
            movement_type=movement_type,
            quantity=quantity,
            uom_id=uom_id,
            unit_cost=unit_cost,
            note=note.strip() if note else None,
            source_type=source_type.strip() if source_type else None,
            source_id=source_id,
            occurred_at=occurred_at or datetime.now(UTC),
        )
        return self.repository.create_movement(movement)
