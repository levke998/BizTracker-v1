"""Catalog read API for product and ingredient costing views."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from decimal import Decimal
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.modules.inventory.infrastructure.orm.inventory_item_model import (
    InventoryItemModel,
)
from app.modules.master_data.infrastructure.orm.category_model import CategoryModel
from app.modules.master_data.infrastructure.orm.product_model import ProductModel
from app.modules.master_data.infrastructure.orm.unit_of_measure_model import (
    UnitOfMeasureModel,
)
from app.modules.production.infrastructure.orm.recipe_model import (
    RecipeIngredientModel,
    RecipeModel,
    RecipeVersionModel,
)

router = APIRouter(prefix="/catalog", tags=["catalog"])


class CatalogBaseSchema(BaseModel):
    """Shared catalog schema configuration."""

    model_config = ConfigDict(from_attributes=True)


class CatalogRecipeIngredientResponse(CatalogBaseSchema):
    """One ingredient line inside a product recipe."""

    inventory_item_id: uuid.UUID
    name: str
    quantity: Decimal
    uom_code: str | None
    unit_cost: Decimal | None
    estimated_cost: Decimal | None


class CatalogProductResponse(CatalogBaseSchema):
    """One product card for the business catalog."""

    id: uuid.UUID
    business_unit_id: uuid.UUID
    category_id: uuid.UUID | None
    category_name: str | None
    sales_uom_id: uuid.UUID | None
    sales_uom_code: str | None
    sales_uom_symbol: str | None
    sku: str | None
    name: str
    product_type: str
    sale_price_gross: Decimal | None
    estimated_unit_cost: Decimal | None
    estimated_margin_amount: Decimal | None
    estimated_margin_percent: Decimal | None
    currency: str
    has_recipe: bool
    recipe_name: str | None
    recipe_yield_quantity: Decimal | None
    recipe_yield_uom_code: str | None
    ingredients: tuple[CatalogRecipeIngredientResponse, ...]
    is_active: bool


class CatalogIngredientResponse(CatalogBaseSchema):
    """One ingredient/material card for the business catalog."""

    id: uuid.UUID
    business_unit_id: uuid.UUID
    name: str
    item_type: str
    uom_id: uuid.UUID
    uom_code: str | None
    uom_symbol: str | None
    default_unit_cost: Decimal | None
    estimated_stock_quantity: Decimal | None
    used_by_product_count: int
    track_stock: bool
    is_active: bool


@dataclass(frozen=True, slots=True)
class _RecipeCost:
    unit_cost: Decimal | None
    recipe_name: str | None
    yield_quantity: Decimal | None
    yield_uom_code: str | None
    ingredients: tuple[CatalogRecipeIngredientResponse, ...]


@router.get("/products", response_model=list[CatalogProductResponse])
def list_catalog_products(
    business_unit_id: uuid.UUID,
    session: Annotated[Session, Depends(get_db_session)],
    active_only: bool = Query(default=True),
) -> list[CatalogProductResponse]:
    """Return products with recipe-derived or direct unit costs."""

    statement = (
        select(ProductModel, CategoryModel.name, UnitOfMeasureModel.code, UnitOfMeasureModel.symbol)
        .outerjoin(CategoryModel, ProductModel.category_id == CategoryModel.id)
        .outerjoin(UnitOfMeasureModel, ProductModel.sales_uom_id == UnitOfMeasureModel.id)
        .where(ProductModel.business_unit_id == business_unit_id)
        .order_by(CategoryModel.name.asc().nulls_last(), ProductModel.name.asc())
    )
    if active_only:
        statement = statement.where(ProductModel.is_active.is_(True))

    ingredient_costs = _load_inventory_unit_costs(session, business_unit_id=business_unit_id)
    product_ids = [row[0].id for row in session.execute(statement).all()]
    recipe_costs = _load_recipe_costs(
        session,
        product_ids=product_ids,
        ingredient_costs=ingredient_costs,
    )

    rows = session.execute(statement).all()
    response: list[CatalogProductResponse] = []
    for product, category_name, sales_uom_code, sales_uom_symbol in rows:
        recipe_cost = recipe_costs.get(product.id)
        estimated_unit_cost = (
            recipe_cost.unit_cost
            if recipe_cost and recipe_cost.unit_cost is not None
            else _decimal_or_none(product.default_unit_cost)
        )
        margin_amount = None
        margin_percent = None
        if product.sale_price_gross is not None and estimated_unit_cost is not None:
            margin_amount = Decimal(product.sale_price_gross) - estimated_unit_cost
            if Decimal(product.sale_price_gross) > 0:
                margin_percent = margin_amount / Decimal(product.sale_price_gross) * Decimal("100")

        response.append(
            CatalogProductResponse(
                id=product.id,
                business_unit_id=product.business_unit_id,
                category_id=product.category_id,
                category_name=category_name,
                sales_uom_id=product.sales_uom_id,
                sales_uom_code=sales_uom_code,
                sales_uom_symbol=sales_uom_symbol,
                sku=product.sku,
                name=product.name,
                product_type=product.product_type,
                sale_price_gross=_decimal_or_none(product.sale_price_gross),
                estimated_unit_cost=estimated_unit_cost,
                estimated_margin_amount=margin_amount,
                estimated_margin_percent=margin_percent,
                currency=product.currency,
                has_recipe=recipe_cost is not None,
                recipe_name=recipe_cost.recipe_name if recipe_cost else None,
                recipe_yield_quantity=recipe_cost.yield_quantity if recipe_cost else None,
                recipe_yield_uom_code=recipe_cost.yield_uom_code if recipe_cost else None,
                ingredients=recipe_cost.ingredients if recipe_cost else (),
                is_active=product.is_active,
            )
        )

    return response


@router.get("/ingredients", response_model=list[CatalogIngredientResponse])
def list_catalog_ingredients(
    business_unit_id: uuid.UUID,
    session: Annotated[Session, Depends(get_db_session)],
    active_only: bool = Query(default=True),
) -> list[CatalogIngredientResponse]:
    """Return inventory ingredients/materials with costing and recipe usage counts."""

    statement = (
        select(InventoryItemModel, UnitOfMeasureModel.code, UnitOfMeasureModel.symbol)
        .outerjoin(UnitOfMeasureModel, InventoryItemModel.uom_id == UnitOfMeasureModel.id)
        .where(InventoryItemModel.business_unit_id == business_unit_id)
        .order_by(InventoryItemModel.name.asc())
    )
    if active_only:
        statement = statement.where(InventoryItemModel.is_active.is_(True))

    usage_counts = _load_ingredient_usage_counts(session, business_unit_id=business_unit_id)
    return [
        CatalogIngredientResponse(
            id=item.id,
            business_unit_id=item.business_unit_id,
            name=item.name,
            item_type=item.item_type,
            uom_id=item.uom_id,
            uom_code=uom_code,
            uom_symbol=uom_symbol,
            default_unit_cost=_decimal_or_none(item.default_unit_cost),
            estimated_stock_quantity=_decimal_or_none(item.estimated_stock_quantity),
            used_by_product_count=usage_counts.get(item.id, 0),
            track_stock=item.track_stock,
            is_active=item.is_active,
        )
        for item, uom_code, uom_symbol in session.execute(statement).all()
    ]


def _load_inventory_unit_costs(
    session: Session,
    *,
    business_unit_id: uuid.UUID,
) -> dict[uuid.UUID, tuple[Decimal, str | None]]:
    rows = session.execute(
        select(InventoryItemModel.id, InventoryItemModel.default_unit_cost, UnitOfMeasureModel.code)
        .outerjoin(UnitOfMeasureModel, InventoryItemModel.uom_id == UnitOfMeasureModel.id)
        .where(InventoryItemModel.business_unit_id == business_unit_id)
    ).all()
    return {
        item_id: (Decimal(unit_cost), uom_code)
        for item_id, unit_cost, uom_code in rows
        if unit_cost is not None
    }


def _load_recipe_costs(
    session: Session,
    *,
    product_ids: list[uuid.UUID],
    ingredient_costs: dict[uuid.UUID, tuple[Decimal, str | None]],
) -> dict[uuid.UUID, _RecipeCost]:
    if not product_ids:
        return {}

    recipe_rows = session.execute(
        select(
            RecipeModel,
            RecipeVersionModel,
            UnitOfMeasureModel.code,
        )
        .join(RecipeVersionModel, RecipeVersionModel.recipe_id == RecipeModel.id)
        .outerjoin(UnitOfMeasureModel, RecipeVersionModel.yield_uom_id == UnitOfMeasureModel.id)
        .where(RecipeModel.product_id.in_(product_ids))
        .where(RecipeModel.is_active.is_(True))
        .where(RecipeVersionModel.is_active.is_(True))
        .order_by(RecipeModel.product_id.asc(), RecipeVersionModel.version_no.desc())
    ).all()

    latest_by_product: dict[uuid.UUID, tuple[RecipeModel, RecipeVersionModel, str | None]] = {}
    for recipe, version, yield_uom_code in recipe_rows:
        latest_by_product.setdefault(recipe.product_id, (recipe, version, yield_uom_code))

    if not latest_by_product:
        return {}

    ingredient_rows = session.execute(
        select(
            RecipeIngredientModel,
            InventoryItemModel.name,
            UnitOfMeasureModel.code,
        )
        .join(InventoryItemModel, RecipeIngredientModel.inventory_item_id == InventoryItemModel.id)
        .outerjoin(UnitOfMeasureModel, RecipeIngredientModel.uom_id == UnitOfMeasureModel.id)
        .where(
            RecipeIngredientModel.recipe_version_id.in_(
                [version.id for _recipe, version, _uom_code in latest_by_product.values()]
            )
        )
        .order_by(InventoryItemModel.name.asc())
    ).all()

    by_version: dict[uuid.UUID, list[tuple[RecipeIngredientModel, str, str | None]]] = {}
    for ingredient, item_name, ingredient_uom_code in ingredient_rows:
        by_version.setdefault(ingredient.recipe_version_id, []).append(
            (ingredient, item_name, ingredient_uom_code)
        )

    results: dict[uuid.UUID, _RecipeCost] = {}
    for product_id, (recipe, version, yield_uom_code) in latest_by_product.items():
        total_cost = Decimal("0")
        ingredient_responses: list[CatalogRecipeIngredientResponse] = []
        for ingredient, item_name, ingredient_uom_code in by_version.get(version.id, []):
            cost_tuple = ingredient_costs.get(ingredient.inventory_item_id)
            unit_cost = cost_tuple[0] if cost_tuple else None
            item_uom_code = cost_tuple[1] if cost_tuple else None
            estimated_cost = None
            if unit_cost is not None:
                converted_quantity = _convert_quantity(
                    Decimal(ingredient.quantity),
                    from_uom=ingredient_uom_code,
                    to_uom=item_uom_code,
                )
                estimated_cost = converted_quantity * unit_cost
                total_cost += estimated_cost

            ingredient_responses.append(
                CatalogRecipeIngredientResponse(
                    inventory_item_id=ingredient.inventory_item_id,
                    name=item_name,
                    quantity=Decimal(ingredient.quantity),
                    uom_code=ingredient_uom_code,
                    unit_cost=unit_cost,
                    estimated_cost=estimated_cost,
                )
            )

        yield_quantity = Decimal(version.yield_quantity)
        unit_cost = total_cost / yield_quantity if yield_quantity > 0 else None
        results[product_id] = _RecipeCost(
            unit_cost=unit_cost,
            recipe_name=recipe.name,
            yield_quantity=yield_quantity,
            yield_uom_code=yield_uom_code,
            ingredients=tuple(ingredient_responses),
        )

    return results


def _load_ingredient_usage_counts(
    session: Session,
    *,
    business_unit_id: uuid.UUID,
) -> dict[uuid.UUID, int]:
    rows = session.execute(
        select(RecipeIngredientModel.inventory_item_id, ProductModel.id)
        .join(RecipeVersionModel, RecipeIngredientModel.recipe_version_id == RecipeVersionModel.id)
        .join(RecipeModel, RecipeVersionModel.recipe_id == RecipeModel.id)
        .join(ProductModel, RecipeModel.product_id == ProductModel.id)
        .where(ProductModel.business_unit_id == business_unit_id)
        .where(ProductModel.is_active.is_(True))
    ).all()
    usage: dict[uuid.UUID, set[uuid.UUID]] = {}
    for inventory_item_id, product_id in rows:
        usage.setdefault(inventory_item_id, set()).add(product_id)
    return {inventory_item_id: len(product_ids) for inventory_item_id, product_ids in usage.items()}


def _convert_quantity(
    quantity: Decimal,
    *,
    from_uom: str | None,
    to_uom: str | None,
) -> Decimal:
    if from_uom == to_uom or from_uom is None or to_uom is None:
        return quantity

    factors = {
        "g": ("mass", Decimal("0.001")),
        "kg": ("mass", Decimal("1")),
        "ml": ("volume", Decimal("0.001")),
        "l": ("volume", Decimal("1")),
    }
    from_factor = factors.get(from_uom)
    to_factor = factors.get(to_uom)
    if from_factor is None or to_factor is None or from_factor[0] != to_factor[0]:
        return quantity

    return (quantity * from_factor[1]) / to_factor[1]


def _decimal_or_none(value: Any) -> Decimal | None:
    return Decimal(value) if value is not None else None
