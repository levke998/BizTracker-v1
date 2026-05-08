"""Recipe write use cases."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
import uuid

from app.modules.production.domain.entities.recipe import RecipeDraft
from app.modules.production.domain.repositories.recipe_repository import RecipeRepository


class RecipeValidationError(ValueError):
    """Raised when a recipe draft violates production rules."""


@dataclass(frozen=True, slots=True)
class SaveActiveProductRecipeCommand:
    """Validate and save a product's next active recipe version."""

    repository: RecipeRepository

    def execute(
        self,
        *,
        product_id: uuid.UUID,
        business_unit_id: uuid.UUID,
        draft: RecipeDraft,
    ) -> None:
        """Persist a new active recipe version after domain-level validation."""

        self._validate(business_unit_id=business_unit_id, draft=draft)
        self.repository.save_active_recipe(product_id=product_id, draft=draft)

    def _validate(self, *, business_unit_id: uuid.UUID, draft: RecipeDraft) -> None:
        if not draft.name.strip():
            raise RecipeValidationError("Recipe name is required.")
        if draft.yield_quantity <= Decimal("0"):
            raise RecipeValidationError("Recipe yield quantity must be positive.")
        if not self.repository.unit_exists(draft.yield_uom_id):
            raise RecipeValidationError("Recipe yield unit of measure was not found.")
        if not draft.ingredients:
            raise RecipeValidationError("Recipe must contain at least one ingredient.")

        seen_items: set[uuid.UUID] = set()
        for ingredient in draft.ingredients:
            if ingredient.quantity <= Decimal("0"):
                raise RecipeValidationError("Recipe ingredient quantity must be positive.")
            if ingredient.inventory_item_id in seen_items:
                raise RecipeValidationError("Recipe cannot contain the same ingredient twice.")
            seen_items.add(ingredient.inventory_item_id)
            if not self.repository.inventory_item_belongs_to_business_unit(
                inventory_item_id=ingredient.inventory_item_id,
                business_unit_id=business_unit_id,
            ):
                raise RecipeValidationError(
                    "Recipe ingredient does not belong to the product business unit."
                )
            if not self.repository.unit_exists(ingredient.uom_id):
                raise RecipeValidationError(
                    "Recipe ingredient unit of measure was not found."
                )
