"""Upsert inventory variance threshold command."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from decimal import Decimal

from app.modules.inventory.domain.entities.inventory_item import (
    InventoryVarianceThreshold,
)
from app.modules.inventory.domain.repositories.inventory_item_repository import (
    InventoryItemRepository,
)


class InventoryVarianceThresholdBusinessUnitNotFoundError(Exception):
    """Raised when the selected business unit does not exist."""


@dataclass(slots=True)
class UpsertInventoryVarianceThresholdCommand:
    """Persist business-unit specific inventory variance thresholds."""

    repository: InventoryItemRepository

    def execute(
        self,
        *,
        business_unit_id: uuid.UUID,
        high_loss_value_threshold: Decimal,
        worsening_percent_threshold: Decimal,
    ) -> InventoryVarianceThreshold:
        if not self.repository.business_unit_exists(business_unit_id):
            raise InventoryVarianceThresholdBusinessUnitNotFoundError(
                f"Business unit {business_unit_id} was not found."
            )

        return self.repository.upsert_variance_threshold(
            business_unit_id=business_unit_id,
            high_loss_value_threshold=high_loss_value_threshold,
            worsening_percent_threshold=worsening_percent_threshold,
        )
