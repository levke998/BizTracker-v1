"""Inventory variance reason summary query."""

from __future__ import annotations

import uuid

from app.modules.inventory.domain.entities.inventory_item import (
    InventoryVarianceReasonSummary,
)
from app.modules.inventory.domain.repositories.inventory_item_repository import (
    InventoryItemRepository,
)


class ListInventoryVarianceReasonSummaryQuery:
    """Return correction movement totals grouped by variance reason."""

    def __init__(self, repository: InventoryItemRepository) -> None:
        self.repository = repository

    def execute(
        self,
        *,
        business_unit_id: uuid.UUID | None = None,
        inventory_item_id: uuid.UUID | None = None,
        limit: int = 20,
    ) -> list[InventoryVarianceReasonSummary]:
        return self.repository.list_variance_reason_summary(
            business_unit_id=business_unit_id,
            inventory_item_id=inventory_item_id,
            limit=limit,
        )
