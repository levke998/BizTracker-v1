"""Build recipe readiness work-queue overview counters."""

from __future__ import annotations

from dataclasses import dataclass
from collections import Counter
import uuid

from app.modules.production.domain.entities.recipe import (
    RecipeReadinessOverview,
    RecipeReadinessStatus,
)
from app.modules.production.domain.repositories.recipe_repository import RecipeRepository


@dataclass(frozen=True, slots=True)
class GetRecipeReadinessOverviewQuery:
    """Application query for aggregate recipe readiness signals."""

    repository: RecipeRepository

    def execute(
        self,
        *,
        business_unit_id: uuid.UUID,
        active_only: bool = True,
    ) -> RecipeReadinessOverview:
        """Return counters without requiring recipe data to exist."""

        summaries = self.repository.list_recipe_summaries(
            business_unit_id=business_unit_id,
            active_only=active_only,
        )
        readiness_counts = Counter(str(summary.readiness_status) for summary in summaries)
        cost_counts = Counter(str(summary.cost_status) for summary in summaries)
        tax_counts = Counter(summary.tax_status for summary in summaries)
        warning_counts: Counter[str] = Counter()
        for summary in summaries:
            warning_counts.update(summary.warnings)

        ready_count = readiness_counts.get(str(RecipeReadinessStatus.READY), 0)
        incomplete_count = len(summaries) - ready_count
        critical_count = sum(
            readiness_counts.get(status, 0)
            for status in (
                str(RecipeReadinessStatus.MISSING_RECIPE),
                str(RecipeReadinessStatus.MISSING_COST),
                str(RecipeReadinessStatus.EMPTY_RECIPE),
            )
        )

        return RecipeReadinessOverview(
            business_unit_id=business_unit_id,
            total_products=len(summaries),
            ready_count=ready_count,
            incomplete_count=incomplete_count,
            critical_count=critical_count,
            readiness_counts=dict(readiness_counts),
            cost_counts=dict(cost_counts),
            tax_counts=dict(tax_counts),
            warning_counts=dict(warning_counts),
            next_actions=_build_next_actions(readiness_counts, warning_counts),
        )


def _build_next_actions(
    readiness_counts: Counter[str],
    warning_counts: Counter[str],
) -> tuple[str, ...]:
    actions: list[str] = []
    if readiness_counts.get(str(RecipeReadinessStatus.MISSING_RECIPE), 0):
        actions.append("create_missing_recipes")
    if readiness_counts.get(str(RecipeReadinessStatus.EMPTY_RECIPE), 0):
        actions.append("fill_empty_recipes")
    if readiness_counts.get(str(RecipeReadinessStatus.MISSING_COST), 0):
        actions.append("fill_missing_ingredient_costs")
    if warning_counts.get("missing_vat_rate", 0):
        actions.append("fill_missing_vat_rates")
    if readiness_counts.get(str(RecipeReadinessStatus.MISSING_STOCK), 0):
        actions.append("review_stock_shortages")
    return tuple(actions)
