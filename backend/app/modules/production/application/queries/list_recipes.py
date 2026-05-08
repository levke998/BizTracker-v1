"""List product recipe readiness and costing."""

from __future__ import annotations

from dataclasses import dataclass
import uuid

from app.modules.production.domain.entities.recipe import RecipeCostSummary
from app.modules.production.domain.repositories.recipe_repository import RecipeRepository


@dataclass(frozen=True, slots=True)
class ListRecipesQuery:
    """Application query for active recipe/readiness rows."""

    repository: RecipeRepository

    def execute(
        self,
        *,
        business_unit_id: uuid.UUID,
        product_id: uuid.UUID | None = None,
        active_only: bool = True,
    ) -> list[RecipeCostSummary]:
        """Return recipe summaries without treating stock shortage as an error."""

        return self.repository.list_recipe_summaries(
            business_unit_id=business_unit_id,
            product_id=product_id,
            active_only=active_only,
        )
