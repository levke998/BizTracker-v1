"""Production recipe domain entities and costing rules."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum
import uuid


class RecipeCostStatus(StrEnum):
    """Costing completeness for a product recipe."""

    COMPLETE = "complete"
    MISSING_COST = "missing_cost"
    NO_RECIPE = "no_recipe"
    EMPTY_RECIPE = "empty_recipe"


class RecipeReadinessStatus(StrEnum):
    """Operational readiness signal. These states never block sales imports."""

    READY = "ready"
    MISSING_RECIPE = "missing_recipe"
    MISSING_COST = "missing_cost"
    MISSING_STOCK = "missing_stock"
    EMPTY_RECIPE = "empty_recipe"


class IngredientStockStatus(StrEnum):
    """Theoretical stock signal for one recipe ingredient."""

    OK = "ok"
    MISSING = "missing"
    INSUFFICIENT = "insufficient"
    UNKNOWN = "unknown"
    NOT_TRACKED = "not_tracked"


@dataclass(frozen=True, slots=True)
class RecipeIngredientDraft:
    """One incoming ingredient line for recipe write use cases."""

    inventory_item_id: uuid.UUID
    quantity: Decimal
    uom_id: uuid.UUID


@dataclass(frozen=True, slots=True)
class RecipeDraft:
    """Incoming recipe payload owned by the production application layer."""

    name: str
    yield_quantity: Decimal
    yield_uom_id: uuid.UUID
    ingredients: tuple[RecipeIngredientDraft, ...]


@dataclass(frozen=True, slots=True)
class RecipeIngredientCost:
    """One ingredient line with theoretical-stock and latest-cost signals."""

    inventory_item_id: uuid.UUID
    inventory_item_name: str
    quantity: Decimal
    uom_id: uuid.UUID
    uom_code: str | None
    item_uom_code: str | None
    converted_quantity: Decimal
    unit_cost: Decimal | None
    estimated_cost: Decimal | None
    estimated_stock_quantity: Decimal | None
    track_stock: bool
    stock_status: IngredientStockStatus
    default_vat_rate_id: uuid.UUID | None = None
    vat_rate_percent: Decimal | None = None
    estimated_vat_amount: Decimal | None = None
    estimated_gross_cost: Decimal | None = None


@dataclass(frozen=True, slots=True)
class RecipeCostSummary:
    """A product's active recipe and cost/readiness state."""

    product_id: uuid.UUID
    business_unit_id: uuid.UUID
    product_name: str
    category_name: str | None
    recipe_id: uuid.UUID | None
    recipe_name: str | None
    version_id: uuid.UUID | None
    version_no: int | None
    yield_quantity: Decimal | None
    yield_uom_id: uuid.UUID | None
    yield_uom_code: str | None
    known_total_cost: Decimal
    total_cost: Decimal | None
    unit_cost: Decimal | None
    cost_status: RecipeCostStatus
    readiness_status: RecipeReadinessStatus
    warnings: tuple[str, ...]
    ingredients: tuple[RecipeIngredientCost, ...]
    known_total_vat_amount: Decimal | None = None
    total_vat_amount: Decimal | None = None
    known_total_gross_cost: Decimal | None = None
    total_gross_cost: Decimal | None = None
    unit_gross_cost: Decimal | None = None
    tax_status: str = "not_available"


@dataclass(frozen=True, slots=True)
class RecipeReadinessOverview:
    """Aggregated recipe work-queue counters for one business unit."""

    business_unit_id: uuid.UUID
    total_products: int
    ready_count: int
    incomplete_count: int
    critical_count: int
    readiness_counts: dict[str, int]
    cost_counts: dict[str, int]
    tax_counts: dict[str, int]
    warning_counts: dict[str, int]
    next_actions: tuple[str, ...]
