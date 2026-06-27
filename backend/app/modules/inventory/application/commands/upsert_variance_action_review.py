"""Upsert inventory variance action review command."""

from __future__ import annotations

import uuid

from app.modules.inventory.domain.entities.inventory_item import (
    InventoryVarianceActionReview,
)
from app.modules.inventory.domain.repositories.inventory_item_repository import (
    InventoryItemRepository,
)


class InventoryVarianceActionReviewBusinessUnitNotFoundError(ValueError):
    """Raised when a review references an unknown business unit."""


class InventoryVarianceActionReviewInvalidStatusError(ValueError):
    """Raised when a review status is not supported."""


class UpsertInventoryVarianceActionReviewCommand:
    """Persist the manual review state of a generated inventory action suggestion."""

    VALID_STATUSES = {"open", "resolved"}

    def __init__(self, repository: InventoryItemRepository) -> None:
        self.repository = repository

    def execute(
        self,
        *,
        business_unit_id: uuid.UUID,
        suggestion_id: str,
        status: str,
        note: str | None = None,
    ) -> InventoryVarianceActionReview:
        if status not in self.VALID_STATUSES:
            raise InventoryVarianceActionReviewInvalidStatusError(
                f"Unsupported inventory action review status: {status}."
            )
        if not self.repository.business_unit_exists(business_unit_id):
            raise InventoryVarianceActionReviewBusinessUnitNotFoundError(
                f"Business unit {business_unit_id} was not found."
            )

        return self.repository.upsert_variance_action_review(
            business_unit_id=business_unit_id,
            suggestion_id=suggestion_id,
            status=status,
            note=note,
        )
