"""Application command for physical stock count corrections."""

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

SOURCE_TYPE_PHYSICAL_STOCK_COUNT = "physical_stock_count"


class PhysicalStockCountBusinessUnitNotFoundError(ValueError):
    """Raised when the business unit does not exist."""


class PhysicalStockCountInventoryItemNotFoundError(ValueError):
    """Raised when the inventory item does not exist."""


class PhysicalStockCountUnitOfMeasureNotFoundError(ValueError):
    """Raised when the unit of measure does not exist."""


class PhysicalStockCountBusinessUnitMismatchError(ValueError):
    """Raised when the inventory item does not belong to the given business unit."""


class PhysicalStockCountUnitOfMeasureMismatchError(ValueError):
    """Raised when the stock count UOM does not match the item UOM."""


@dataclass(frozen=True, slots=True)
class PhysicalStockCountResult:
    """Physical stock count correction result."""

    inventory_item_id: uuid.UUID
    business_unit_id: uuid.UUID
    previous_quantity: Decimal
    counted_quantity: Decimal
    adjustment_quantity: Decimal
    movement: InventoryMovement


@dataclass(slots=True)
class RegisterPhysicalStockCountCommand:
    """Register one physical count and create the required stock correction."""

    repository: InventoryItemRepository

    def execute(
        self,
        *,
        business_unit_id: uuid.UUID,
        inventory_item_id: uuid.UUID,
        counted_quantity: Decimal,
        uom_id: uuid.UUID,
        reason_code: str,
        occurred_at: datetime | None = None,
        note: str | None = None,
    ) -> PhysicalStockCountResult:
        if not self.repository.business_unit_exists(business_unit_id):
            raise PhysicalStockCountBusinessUnitNotFoundError(
                f"Business unit '{business_unit_id}' was not found."
            )

        inventory_item = self.repository.get_by_id(inventory_item_id)
        if inventory_item is None:
            raise PhysicalStockCountInventoryItemNotFoundError(
                f"Inventory item '{inventory_item_id}' was not found."
            )

        if not self.repository.unit_of_measure_exists(uom_id):
            raise PhysicalStockCountUnitOfMeasureNotFoundError(
                f"Unit of measure '{uom_id}' was not found."
            )

        if inventory_item.business_unit_id != business_unit_id:
            raise PhysicalStockCountBusinessUnitMismatchError(
                "Inventory item does not belong to the given business unit."
            )

        if inventory_item.uom_id != uom_id:
            raise PhysicalStockCountUnitOfMeasureMismatchError(
                "Physical count unit of measure must match the inventory item unit of measure."
            )

        previous_quantity = self._current_quantity(
            business_unit_id=business_unit_id,
            inventory_item_id=inventory_item_id,
        )
        counted = counted_quantity.quantize(Decimal("0.001"))
        adjustment_quantity = (counted - previous_quantity).quantize(Decimal("0.001"))
        movement_type = "adjustment" if adjustment_quantity >= 0 else "waste"
        movement_quantity = abs(adjustment_quantity)
        occurred = occurred_at or datetime.now(UTC)

        movement = self.repository.create_movement(
            movement=NewInventoryMovement(
                business_unit_id=business_unit_id,
                inventory_item_id=inventory_item_id,
                movement_type=movement_type,
                quantity=movement_quantity,
                uom_id=uom_id,
                unit_cost=None,
                reason_code=reason_code.strip(),
                note=note.strip() if note else None,
                source_type=SOURCE_TYPE_PHYSICAL_STOCK_COUNT,
                source_id=uuid.uuid4(),
                occurred_at=occurred,
            )
        )

        return PhysicalStockCountResult(
            inventory_item_id=inventory_item_id,
            business_unit_id=business_unit_id,
            previous_quantity=previous_quantity,
            counted_quantity=counted,
            adjustment_quantity=adjustment_quantity,
            movement=movement,
        )

    def _current_quantity(
        self,
        *,
        business_unit_id: uuid.UUID,
        inventory_item_id: uuid.UUID,
    ) -> Decimal:
        rows = self.repository.list_stock_levels(
            business_unit_id=business_unit_id,
            inventory_item_id=inventory_item_id,
            limit=1,
        )
        if not rows:
            return Decimal("0.000")
        return Decimal(rows[0].current_quantity).quantize(Decimal("0.001"))
