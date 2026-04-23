"""Inventory theoretical stock list query."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from app.modules.inventory.domain.entities.inventory_item import (
    InventoryTheoreticalStock,
)
from app.modules.inventory.domain.repositories.inventory_item_repository import (
    InventoryItemRepository,
)

THEORETICAL_STOCK_ESTIMATION_BASIS = "not_configured"


@dataclass(slots=True)
class ListInventoryTheoreticalStockQuery:
    """Return an explicit theoretical-stock read model without mixing it with actual stock."""

    repository: InventoryItemRepository

    def execute(
        self,
        *,
        business_unit_id: uuid.UUID | None = None,
        inventory_item_id: uuid.UUID | None = None,
        item_type: str | None = None,
        limit: int = 50,
    ) -> list[InventoryTheoreticalStock]:
        stock_levels = self.repository.list_stock_levels(
            business_unit_id=business_unit_id,
            inventory_item_id=inventory_item_id,
            item_type=item_type,
            limit=limit,
        )

        return [
            InventoryTheoreticalStock(
                inventory_item_id=item.inventory_item_id,
                business_unit_id=item.business_unit_id,
                name=item.name,
                item_type=item.item_type,
                uom_id=item.uom_id,
                track_stock=item.track_stock,
                is_active=item.is_active,
                actual_quantity=item.current_quantity,
                theoretical_quantity=None,
                variance_quantity=None,
                last_actual_movement_at=item.last_movement_at,
                last_estimated_event_at=None,
                estimation_basis=THEORETICAL_STOCK_ESTIMATION_BASIS,
            )
            for item in stock_levels
        ]
