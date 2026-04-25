"""Catalog read API for product and ingredient costing views."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from decimal import Decimal
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.modules.inventory.infrastructure.orm.inventory_item_model import (
    InventoryItemModel,
)
from app.modules.master_data.infrastructure.orm.business_unit_model import (
    BusinessUnitModel,
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


class CatalogRecipeIngredientRequest(BaseModel):
    """One editable ingredient quantity for a recipe version."""

    inventory_item_id: uuid.UUID
    quantity: Decimal = Field(gt=0)
    uom_id: uuid.UUID


class CatalogRecipeRequest(BaseModel):
    """Editable recipe payload. Updates create a new active version."""

    name: str = Field(min_length=1, max_length=200)
    yield_quantity: Decimal = Field(gt=0)
    yield_uom_id: uuid.UUID
    ingredients: list[CatalogRecipeIngredientRequest] = Field(default_factory=list)


class CatalogProductCreateRequest(BaseModel):
    """Create one sellable product with an optional first recipe."""

    business_unit_id: uuid.UUID
    category_id: uuid.UUID | None = None
    sales_uom_id: uuid.UUID | None = None
    sku: str | None = Field(default=None, max_length=64)
    name: str = Field(min_length=1, max_length=200)
    product_type: str = Field(min_length=1, max_length=50)
    sale_price_gross: Decimal | None = Field(default=None, ge=0)
    default_unit_cost: Decimal | None = Field(default=None, ge=0)
    currency: str = Field(default="HUF", min_length=3, max_length=3)
    is_active: bool = True
    recipe: CatalogRecipeRequest | None = None


class CatalogProductUpdateRequest(BaseModel):
    """Update product fields and optionally replace the active recipe version."""

    category_id: uuid.UUID | None = None
    sales_uom_id: uuid.UUID | None = None
    sku: str | None = Field(default=None, max_length=64)
    name: str = Field(min_length=1, max_length=200)
    product_type: str = Field(min_length=1, max_length=50)
    sale_price_gross: Decimal | None = Field(default=None, ge=0)
    default_unit_cost: Decimal | None = Field(default=None, ge=0)
    currency: str = Field(default="HUF", min_length=3, max_length=3)
    is_active: bool = True
    recipe: CatalogRecipeRequest | None = None


class CatalogIngredientCreateRequest(BaseModel):
    """Create one catalog ingredient/material."""

    business_unit_id: uuid.UUID
    name: str = Field(min_length=1, max_length=150)
    item_type: str = Field(min_length=1, max_length=50)
    uom_id: uuid.UUID
    track_stock: bool = True
    default_unit_cost: Decimal | None = Field(default=None, ge=0)
    estimated_stock_quantity: Decimal | None = Field(default=None, ge=0)
    is_active: bool = True


class CatalogIngredientUpdateRequest(BaseModel):
    """Update one catalog ingredient/material."""

    name: str = Field(min_length=1, max_length=150)
    item_type: str = Field(min_length=1, max_length=50)
    uom_id: uuid.UUID
    track_stock: bool = True
    default_unit_cost: Decimal | None = Field(default=None, ge=0)
    estimated_stock_quantity: Decimal | None = Field(default=None, ge=0)
    is_active: bool = True


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


@router.post(
    "/products",
    response_model=CatalogProductResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_catalog_product(
    payload: CatalogProductCreateRequest,
    session: Annotated[Session, Depends(get_db_session)],
) -> CatalogProductResponse:
    """Create one catalog product, optionally with an initial recipe."""

    _validate_business_unit(session, payload.business_unit_id)
    _validate_product_refs(
        session,
        business_unit_id=payload.business_unit_id,
        category_id=payload.category_id,
        sales_uom_id=payload.sales_uom_id,
    )
    if payload.recipe is not None:
        _validate_recipe_payload(
            session,
            business_unit_id=payload.business_unit_id,
            recipe=payload.recipe,
        )

    product = ProductModel(
        business_unit_id=payload.business_unit_id,
        category_id=payload.category_id,
        sales_uom_id=payload.sales_uom_id,
        sku=_blank_to_none(payload.sku),
        name=payload.name.strip(),
        product_type=payload.product_type.strip(),
        sale_price_gross=payload.sale_price_gross,
        default_unit_cost=payload.default_unit_cost,
        currency=payload.currency.upper(),
        is_active=payload.is_active,
    )
    session.add(product)
    session.flush()

    if payload.recipe is not None:
        _replace_active_recipe(session, product=product, recipe_payload=payload.recipe)

    session.commit()
    return _get_catalog_product_response(session, product_id=product.id)


@router.patch("/products/{product_id}", response_model=CatalogProductResponse)
def update_catalog_product(
    product_id: uuid.UUID,
    payload: CatalogProductUpdateRequest,
    session: Annotated[Session, Depends(get_db_session)],
) -> CatalogProductResponse:
    """Update one product and optionally write a new active recipe version."""

    product = session.get(ProductModel, product_id)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")

    _validate_product_refs(
        session,
        business_unit_id=product.business_unit_id,
        category_id=payload.category_id,
        sales_uom_id=payload.sales_uom_id,
    )
    if payload.recipe is not None:
        _validate_recipe_payload(
            session,
            business_unit_id=product.business_unit_id,
            recipe=payload.recipe,
        )

    product.category_id = payload.category_id
    product.sales_uom_id = payload.sales_uom_id
    product.sku = _blank_to_none(payload.sku)
    product.name = payload.name.strip()
    product.product_type = payload.product_type.strip()
    product.sale_price_gross = payload.sale_price_gross
    product.default_unit_cost = payload.default_unit_cost
    product.currency = payload.currency.upper()
    product.is_active = payload.is_active

    if payload.recipe is not None:
        _replace_active_recipe(session, product=product, recipe_payload=payload.recipe)

    session.commit()
    return _get_catalog_product_response(session, product_id=product.id)


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


@router.post(
    "/ingredients",
    response_model=CatalogIngredientResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_catalog_ingredient(
    payload: CatalogIngredientCreateRequest,
    session: Annotated[Session, Depends(get_db_session)],
) -> CatalogIngredientResponse:
    """Create one ingredient/material with costing and estimated stock fields."""

    _validate_business_unit(session, payload.business_unit_id)
    _validate_unit_of_measure(session, payload.uom_id)
    _validate_unique_inventory_name(
        session,
        business_unit_id=payload.business_unit_id,
        name=payload.name,
    )
    item = InventoryItemModel(
        business_unit_id=payload.business_unit_id,
        name=payload.name.strip(),
        item_type=payload.item_type.strip(),
        uom_id=payload.uom_id,
        track_stock=payload.track_stock,
        default_unit_cost=payload.default_unit_cost,
        estimated_stock_quantity=payload.estimated_stock_quantity,
        is_active=payload.is_active,
    )
    session.add(item)
    session.commit()
    return _get_catalog_ingredient_response(session, inventory_item_id=item.id)


@router.patch("/ingredients/{inventory_item_id}", response_model=CatalogIngredientResponse)
def update_catalog_ingredient(
    inventory_item_id: uuid.UUID,
    payload: CatalogIngredientUpdateRequest,
    session: Annotated[Session, Depends(get_db_session)],
) -> CatalogIngredientResponse:
    """Update one ingredient/material cost and estimated stock."""

    item = session.get(InventoryItemModel, inventory_item_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ingredient not found.")

    _validate_unit_of_measure(session, payload.uom_id)
    _validate_unique_inventory_name(
        session,
        business_unit_id=item.business_unit_id,
        name=payload.name,
        exclude_inventory_item_id=inventory_item_id,
    )
    item.name = payload.name.strip()
    item.item_type = payload.item_type.strip()
    item.uom_id = payload.uom_id
    item.track_stock = payload.track_stock
    item.default_unit_cost = payload.default_unit_cost
    item.estimated_stock_quantity = payload.estimated_stock_quantity
    item.is_active = payload.is_active

    session.commit()
    return _get_catalog_ingredient_response(session, inventory_item_id=item.id)


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


def _get_catalog_product_response(
    session: Session,
    *,
    product_id: uuid.UUID,
) -> CatalogProductResponse:
    product = session.get(ProductModel, product_id)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")

    rows = list_catalog_products(
        business_unit_id=product.business_unit_id,
        session=session,
        active_only=False,
    )
    for row in rows:
        if row.id == product_id:
            return row
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")


def _get_catalog_ingredient_response(
    session: Session,
    *,
    inventory_item_id: uuid.UUID,
) -> CatalogIngredientResponse:
    item = session.get(InventoryItemModel, inventory_item_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ingredient not found.")

    rows = list_catalog_ingredients(
        business_unit_id=item.business_unit_id,
        session=session,
        active_only=False,
    )
    for row in rows:
        if row.id == inventory_item_id:
            return row
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ingredient not found.")


def _validate_product_refs(
    session: Session,
    *,
    business_unit_id: uuid.UUID,
    category_id: uuid.UUID | None,
    sales_uom_id: uuid.UUID | None,
) -> None:
    if category_id is not None:
        category = session.get(CategoryModel, category_id)
        if category is None or category.business_unit_id != business_unit_id:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Category does not belong to the selected business unit.",
            )
    if sales_uom_id is not None:
        _validate_unit_of_measure(session, sales_uom_id)


def _validate_business_unit(session: Session, business_unit_id: uuid.UUID) -> None:
    if session.get(BusinessUnitModel, business_unit_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business unit was not found.",
        )


def _validate_recipe_payload(
    session: Session,
    *,
    business_unit_id: uuid.UUID,
    recipe: CatalogRecipeRequest,
) -> None:
    _validate_unit_of_measure(session, recipe.yield_uom_id)
    if not recipe.ingredients:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Recipe must contain at least one ingredient.",
        )

    seen_items: set[uuid.UUID] = set()
    for ingredient in recipe.ingredients:
        if ingredient.inventory_item_id in seen_items:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Recipe cannot contain the same ingredient twice.",
            )
        seen_items.add(ingredient.inventory_item_id)
        item = session.get(InventoryItemModel, ingredient.inventory_item_id)
        if item is None or item.business_unit_id != business_unit_id:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Recipe ingredient does not belong to the product business unit.",
            )
        _validate_unit_of_measure(session, ingredient.uom_id)


def _replace_active_recipe(
    session: Session,
    *,
    product: ProductModel,
    recipe_payload: CatalogRecipeRequest,
) -> None:
    recipe = session.scalar(
        select(RecipeModel)
        .where(RecipeModel.product_id == product.id)
        .where(RecipeModel.is_active.is_(True))
        .order_by(RecipeModel.created_at.asc())
    )
    if recipe is None:
        recipe = RecipeModel(
            product_id=product.id,
            name=recipe_payload.name.strip(),
            is_active=True,
        )
        session.add(recipe)
        session.flush()
    else:
        recipe.name = recipe_payload.name.strip()

    latest_version_no = session.scalar(
        select(RecipeVersionModel.version_no)
        .where(RecipeVersionModel.recipe_id == recipe.id)
        .order_by(RecipeVersionModel.version_no.desc())
        .limit(1)
    )
    session.execute(
        select(RecipeVersionModel)
        .where(RecipeVersionModel.recipe_id == recipe.id)
        .where(RecipeVersionModel.is_active.is_(True))
    )
    active_versions = session.scalars(
        select(RecipeVersionModel)
        .where(RecipeVersionModel.recipe_id == recipe.id)
        .where(RecipeVersionModel.is_active.is_(True))
    ).all()
    for version in active_versions:
        version.is_active = False

    version = RecipeVersionModel(
        recipe_id=recipe.id,
        version_no=(latest_version_no or 0) + 1,
        is_active=True,
        yield_quantity=recipe_payload.yield_quantity,
        yield_uom_id=recipe_payload.yield_uom_id,
        notes="Catalog edit",
    )
    session.add(version)
    session.flush()

    for ingredient in recipe_payload.ingredients:
        session.add(
            RecipeIngredientModel(
                recipe_version_id=version.id,
                inventory_item_id=ingredient.inventory_item_id,
                quantity=ingredient.quantity,
                uom_id=ingredient.uom_id,
            )
        )


def _validate_unit_of_measure(session: Session, uom_id: uuid.UUID) -> None:
    if session.get(UnitOfMeasureModel, uom_id) is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Unit of measure was not found.",
        )


def _validate_unique_inventory_name(
    session: Session,
    *,
    business_unit_id: uuid.UUID,
    name: str,
    exclude_inventory_item_id: uuid.UUID | None = None,
) -> None:
    statement = (
        select(InventoryItemModel.id)
        .where(InventoryItemModel.business_unit_id == business_unit_id)
        .where(InventoryItemModel.name == name.strip())
    )
    if exclude_inventory_item_id is not None:
        statement = statement.where(InventoryItemModel.id != exclude_inventory_item_id)
    if session.scalar(statement) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An ingredient with this name already exists in the business unit.",
        )


def _blank_to_none(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


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
