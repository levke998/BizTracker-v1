"""Inventory variance threshold query."""

from __future__ import annotations

import uuid

from app.modules.inventory.domain.entities.inventory_item import (
    InventoryVarianceThreshold,
)
from app.modules.inventory.domain.repositories.inventory_item_repository import (
    InventoryItemRepository,
)


class GetInventoryVarianceThresholdQuery:
    """Return effective inventory variance thresholds for one business unit."""

    def __init__(self, repository: InventoryItemRepository) -> None:
        self.repository = repository

    def execute(self, *, business_unit_id: uuid.UUID) -> InventoryVarianceThreshold:
        return self.repository.get_variance_threshold(
            business_unit_id=business_unit_id,
        )
