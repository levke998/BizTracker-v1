"""Repository contract for production recipe read models."""

from __future__ import annotations

from typing import Protocol
import uuid

from app.modules.production.domain.entities.recipe import RecipeCostSummary, RecipeDraft


class RecipeRepository(Protocol):
    """Access contract for product recipe costing, validation and writes."""

    def list_recipe_summaries(
        self,
        *,
        business_unit_id: uuid.UUID,
        product_id: uuid.UUID | None = None,
        active_only: bool = True,
    ) -> list[RecipeCostSummary]:
        """Return product recipe summaries for one business unit."""

    def unit_exists(self, uom_id: uuid.UUID) -> bool:
        """Return whether a unit of measure exists."""

    def inventory_item_belongs_to_business_unit(
        self,
        *,
        inventory_item_id: uuid.UUID,
        business_unit_id: uuid.UUID,
    ) -> bool:
        """Return whether an inventory item can be used in the recipe."""

    def save_active_recipe(
        self,
        *,
        product_id: uuid.UUID,
        draft: RecipeDraft,
    ) -> None:
        """Create a new active recipe version for the product."""
