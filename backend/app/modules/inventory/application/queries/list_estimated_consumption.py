"""Inventory estimated consumption audit list query."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from app.modules.inventory.domain.entities.inventory_item import (
    EstimatedConsumptionAudit,
)
from app.modules.inventory.domain.repositories.inventory_item_repository import (
    InventoryItemRepository,
)


@dataclass(slots=True)
class ListEstimatedConsumptionAuditQuery:
    """Return estimated stock consumption audit rows."""

    repository: InventoryItemRepository

    def execute(
        self,
        *,
        business_unit_id: uuid.UUID | None = None,
        inventory_item_id: uuid.UUID | None = None,
        product_id: uuid.UUID | None = None,
        source_type: str | None = None,
        limit: int = 50,
    ) -> list[EstimatedConsumptionAudit]:
        return self.repository.list_estimated_consumption(
            business_unit_id=business_unit_id,
            inventory_item_id=inventory_item_id,
            product_id=product_id,
            source_type=source_type,
            limit=limit,
        )
