"""Inventory variance item summary query."""

from __future__ import annotations

import uuid

from app.modules.inventory.domain.entities.inventory_item import (
    InventoryVarianceItemSummary,
)
from app.modules.inventory.domain.repositories.inventory_item_repository import (
    InventoryItemRepository,
)


class ListInventoryVarianceItemSummaryQuery:
    """Return correction totals grouped by inventory item."""

    def __init__(self, repository: InventoryItemRepository) -> None:
        self.repository = repository

    def execute(
        self,
        *,
        business_unit_id: uuid.UUID | None = None,
        limit: int = 20,
    ) -> list[InventoryVarianceItemSummary]:
        return self.repository.list_variance_item_summary(
            business_unit_id=business_unit_id,
            limit=limit,
        )
