"""API schemas for production recipe readiness."""

from __future__ import annotations

from decimal import Decimal
import uuid

from pydantic import BaseModel, ConfigDict, Field


class ProductionBaseSchema(BaseModel):
    """Shared production schema configuration."""

    model_config = ConfigDict(from_attributes=True)


class RecipeIngredientCostResponse(ProductionBaseSchema):
    """One ingredient line in a recipe cost summary."""

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
    stock_status: str


class RecipeIngredientSaveRequest(BaseModel):
    """One editable ingredient line for a recipe write request."""

    inventory_item_id: uuid.UUID
    quantity: Decimal = Field(gt=0)
    uom_id: uuid.UUID


class RecipeSaveRequest(BaseModel):
    """Payload for saving the product's next active recipe version."""

    name: str = Field(min_length=1, max_length=200)
    yield_quantity: Decimal = Field(gt=0)
    yield_uom_id: uuid.UUID
    ingredients: list[RecipeIngredientSaveRequest] = Field(default_factory=list)


class RecipeCostSummaryResponse(ProductionBaseSchema):
    """One product recipe readiness row."""

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
    cost_status: str
    readiness_status: str
    warnings: tuple[str, ...]
    ingredients: tuple[RecipeIngredientCostResponse, ...]
