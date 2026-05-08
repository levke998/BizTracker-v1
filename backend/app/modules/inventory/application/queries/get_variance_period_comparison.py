"""Inventory variance period comparison query."""

from __future__ import annotations

import uuid
from decimal import Decimal

from app.modules.inventory.domain.entities.inventory_item import (
    InventoryVariancePeriodComparison,
)
from app.modules.inventory.domain.repositories.inventory_item_repository import (
    InventoryItemRepository,
)


class GetInventoryVariancePeriodComparisonQuery:
    """Return current vs previous period variance controlling metrics."""

    def __init__(self, repository: InventoryItemRepository) -> None:
        self.repository = repository

    def execute(
        self,
        *,
        business_unit_id: uuid.UUID | None = None,
        inventory_item_id: uuid.UUID | None = None,
        days: int = 30,
        high_loss_value_threshold: Decimal | None = None,
        worsening_percent_threshold: Decimal | None = None,
    ) -> InventoryVariancePeriodComparison:
        return self.repository.get_variance_period_comparison(
            business_unit_id=business_unit_id,
            inventory_item_id=inventory_item_id,
            days=days,
            high_loss_value_threshold=high_loss_value_threshold,
            worsening_percent_threshold=worsening_percent_threshold,
        )
