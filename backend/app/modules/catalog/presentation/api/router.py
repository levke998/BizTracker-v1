"""Catalog read API for product and ingredient costing views."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
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
from app.modules.master_data.infrastructure.orm.vat_rate_model import VatRateModel
from app.modules.production.application.commands.create_recipe import (
    RecipeValidationError,
    SaveActiveProductRecipeCommand,
)
from app.modules.production.domain.entities.recipe import RecipeDraft, RecipeIngredientDraft
from app.modules.production.infrastructure.orm.recipe_model import (
    RecipeIngredientModel,
    RecipeModel,
    RecipeVersionModel,
)
from app.modules.production.infrastructure.repositories.sqlalchemy_recipe_repository import (
    SqlAlchemyRecipeRepository,
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
    default_vat_rate_id: uuid.UUID | None
    vat_rate_name: str | None
    vat_rate_percent: Decimal | None
    sku: str | None
    name: str
    product_type: str
    sale_price_gross: Decimal | None
    sale_price_last_seen_at: datetime | None
    sale_price_source: str | None
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
    default_vat_rate_id: uuid.UUID | None
    vat_rate_name: str | None
    vat_rate_percent: Decimal | None
    default_unit_cost: Decimal | None
    default_unit_cost_last_seen_at: datetime | None
    default_unit_cost_source_type: str | None
    default_unit_cost_source_id: uuid.UUID | None
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
    default_vat_rate_id: uuid.UUID | None = None
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
    default_vat_rate_id: uuid.UUID | None = None
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
    default_vat_rate_id: uuid.UUID | None = None
    track_stock: bool = True
    default_unit_cost: Decimal | None = Field(default=None, ge=0)
    estimated_stock_quantity: Decimal | None = Field(default=None, ge=0)
    is_active: bool = True


class CatalogIngredientUpdateRequest(BaseModel):
    """Update one catalog ingredient/material."""

    name: str = Field(min_length=1, max_length=150)
    item_type: str = Field(min_length=1, max_length=50)
    uom_id: uuid.UUID
    default_vat_rate_id: uuid.UUID | None = None
    track_stock: bool = True
    default_unit_cost: Decimal | None = Field(default=None, ge=0)
    estimated_stock_quantity: Decimal | None = Field(default=None, ge=0)
    is_active: bool = True


@router.get("/products", response_model=list[CatalogProductResponse])
def list_catalog_products(
    business_unit_id: uuid.UUID,
    session: Annotated[Session, Depends(get_db_session)],
    active_only: bool = Query(default=True),
) -> list[CatalogProductResponse]:
    """Return products with recipe-derived or direct unit costs."""

    statement = (
        select(
            ProductModel,
            CategoryModel.name,
            UnitOfMeasureModel.code,
            UnitOfMeasureModel.symbol,
            VatRateModel.name,
            VatRateModel.rate_percent,
        )
        .outerjoin(CategoryModel, ProductModel.category_id == CategoryModel.id)
        .outerjoin(UnitOfMeasureModel, ProductModel.sales_uom_id == UnitOfMeasureModel.id)
        .outerjoin(VatRateModel, ProductModel.default_vat_rate_id == VatRateModel.id)
        .where(ProductModel.business_unit_id == business_unit_id)
        .order_by(CategoryModel.name.asc().nulls_last(), ProductModel.name.asc())
    )
    if active_only:
        statement = statement.where(ProductModel.is_active.is_(True))

    recipe_summaries = {
        summary.product_id: summary
        for summary in SqlAlchemyRecipeRepository(session).list_recipe_summaries(
            business_unit_id=business_unit_id,
            active_only=active_only,
        )
    }

    rows = session.execute(statement).all()
    response: list[CatalogProductResponse] = []
    for product, category_name, sales_uom_code, sales_uom_symbol, vat_rate_name, vat_rate_percent in rows:
        recipe_summary = recipe_summaries.get(product.id)
        estimated_unit_cost = (
            recipe_summary.unit_cost
            if recipe_summary is not None and recipe_summary.unit_cost is not None
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
                default_vat_rate_id=product.default_vat_rate_id,
                vat_rate_name=vat_rate_name,
                vat_rate_percent=_decimal_or_none(vat_rate_percent),
                sku=product.sku,
                name=product.name,
                product_type=product.product_type,
                sale_price_gross=_decimal_or_none(product.sale_price_gross),
                sale_price_last_seen_at=product.sale_price_last_seen_at,
                sale_price_source=product.sale_price_source,
                estimated_unit_cost=estimated_unit_cost,
                estimated_margin_amount=margin_amount,
                estimated_margin_percent=margin_percent,
                currency=product.currency,
                has_recipe=(
                    recipe_summary is not None and recipe_summary.recipe_id is not None
                ),
                recipe_name=recipe_summary.recipe_name if recipe_summary else None,
                recipe_yield_quantity=(
                    recipe_summary.yield_quantity if recipe_summary else None
                ),
                recipe_yield_uom_code=(
                    recipe_summary.yield_uom_code if recipe_summary else None
                ),
                ingredients=(
                    tuple(
                        CatalogRecipeIngredientResponse(
                            inventory_item_id=ingredient.inventory_item_id,
                            name=ingredient.inventory_item_name,
                            quantity=ingredient.quantity,
                            uom_code=ingredient.uom_code,
                            unit_cost=ingredient.unit_cost,
                            estimated_cost=ingredient.estimated_cost,
                        )
                        for ingredient in recipe_summary.ingredients
                    )
                    if recipe_summary
                    else ()
                ),
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
        default_vat_rate_id=payload.default_vat_rate_id,
    )
    product = ProductModel(
        business_unit_id=payload.business_unit_id,
        category_id=payload.category_id,
        sales_uom_id=payload.sales_uom_id,
        default_vat_rate_id=payload.default_vat_rate_id,
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
        _save_active_recipe(
            session,
            product=product,
            recipe_payload=payload.recipe,
        )

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
        default_vat_rate_id=payload.default_vat_rate_id,
    )
    product.category_id = payload.category_id
    product.sales_uom_id = payload.sales_uom_id
    product.default_vat_rate_id = payload.default_vat_rate_id
    product.sku = _blank_to_none(payload.sku)
    product.name = payload.name.strip()
    product.product_type = payload.product_type.strip()
    product.sale_price_gross = payload.sale_price_gross
    product.default_unit_cost = payload.default_unit_cost
    product.currency = payload.currency.upper()
    product.is_active = payload.is_active

    if payload.recipe is not None:
        _save_active_recipe(
            session,
            product=product,
            recipe_payload=payload.recipe,
        )

    session.commit()
    return _get_catalog_product_response(session, product_id=product.id)


@router.delete("/products/{product_id}", response_model=CatalogProductResponse)
def archive_catalog_product(
    product_id: uuid.UUID,
    session: Annotated[Session, Depends(get_db_session)],
) -> CatalogProductResponse:
    """Archive one product while preserving source-data and sales history."""

    product = session.get(ProductModel, product_id)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")

    product.is_active = False
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
        select(
            InventoryItemModel,
            UnitOfMeasureModel.code,
            UnitOfMeasureModel.symbol,
            VatRateModel.name,
            VatRateModel.rate_percent,
        )
        .outerjoin(UnitOfMeasureModel, InventoryItemModel.uom_id == UnitOfMeasureModel.id)
        .outerjoin(VatRateModel, InventoryItemModel.default_vat_rate_id == VatRateModel.id)
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
            default_vat_rate_id=item.default_vat_rate_id,
            vat_rate_name=vat_rate_name,
            vat_rate_percent=_decimal_or_none(vat_rate_percent),
            default_unit_cost=_decimal_or_none(item.default_unit_cost),
            default_unit_cost_last_seen_at=item.default_unit_cost_last_seen_at,
            default_unit_cost_source_type=item.default_unit_cost_source_type,
            default_unit_cost_source_id=item.default_unit_cost_source_id,
            estimated_stock_quantity=_decimal_or_none(item.estimated_stock_quantity),
            used_by_product_count=usage_counts.get(item.id, 0),
            track_stock=item.track_stock,
            is_active=item.is_active,
        )
        for item, uom_code, uom_symbol, vat_rate_name, vat_rate_percent in session.execute(statement).all()
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
    _validate_vat_rate(session, payload.default_vat_rate_id)
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
        default_vat_rate_id=payload.default_vat_rate_id,
        track_stock=payload.track_stock,
        default_unit_cost=payload.default_unit_cost,
        default_unit_cost_last_seen_at=(
            datetime.now(UTC) if payload.default_unit_cost is not None else None
        ),
        default_unit_cost_source_type=(
            "manual" if payload.default_unit_cost is not None else None
        ),
        default_unit_cost_source_id=None,
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
    _validate_vat_rate(session, payload.default_vat_rate_id)
    _validate_unique_inventory_name(
        session,
        business_unit_id=item.business_unit_id,
        name=payload.name,
        exclude_inventory_item_id=inventory_item_id,
    )
    item.name = payload.name.strip()
    item.item_type = payload.item_type.strip()
    item.uom_id = payload.uom_id
    item.default_vat_rate_id = payload.default_vat_rate_id
    item.track_stock = payload.track_stock
    current_cost = _decimal_or_none(item.default_unit_cost)
    item.default_unit_cost = payload.default_unit_cost
    if payload.default_unit_cost is None:
        item.default_unit_cost_last_seen_at = None
        item.default_unit_cost_source_type = None
        item.default_unit_cost_source_id = None
    elif current_cost != payload.default_unit_cost:
        item.default_unit_cost_last_seen_at = datetime.now(UTC)
        item.default_unit_cost_source_type = "manual"
        item.default_unit_cost_source_id = None
    item.estimated_stock_quantity = payload.estimated_stock_quantity
    item.is_active = payload.is_active

    session.commit()
    return _get_catalog_ingredient_response(session, inventory_item_id=item.id)


@router.delete("/ingredients/{inventory_item_id}", response_model=CatalogIngredientResponse)
def archive_catalog_ingredient(
    inventory_item_id: uuid.UUID,
    session: Annotated[Session, Depends(get_db_session)],
) -> CatalogIngredientResponse:
    """Archive one ingredient/material without deleting historical references."""

    item = session.get(InventoryItemModel, inventory_item_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ingredient not found.")

    item.is_active = False
    session.commit()
    return _get_catalog_ingredient_response(session, inventory_item_id=item.id)


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
    default_vat_rate_id: uuid.UUID | None,
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
    _validate_vat_rate(session, default_vat_rate_id)


def _validate_business_unit(session: Session, business_unit_id: uuid.UUID) -> None:
    if session.get(BusinessUnitModel, business_unit_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business unit was not found.",
        )


def _save_active_recipe(
    session: Session,
    *,
    product: ProductModel,
    recipe_payload: CatalogRecipeRequest,
) -> None:
    command = SaveActiveProductRecipeCommand(
        repository=SqlAlchemyRecipeRepository(session),
    )
    try:
        command.execute(
            product_id=product.id,
            business_unit_id=product.business_unit_id,
            draft=_to_recipe_draft(recipe_payload),
        )
    except RecipeValidationError as exc:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


def _to_recipe_draft(recipe_payload: CatalogRecipeRequest) -> RecipeDraft:
    return RecipeDraft(
        name=recipe_payload.name,
        yield_quantity=recipe_payload.yield_quantity,
        yield_uom_id=recipe_payload.yield_uom_id,
        ingredients=tuple(
            RecipeIngredientDraft(
                inventory_item_id=ingredient.inventory_item_id,
                quantity=ingredient.quantity,
                uom_id=ingredient.uom_id,
            )
            for ingredient in recipe_payload.ingredients
        ),
    )


def _validate_unit_of_measure(session: Session, uom_id: uuid.UUID) -> None:
    if session.get(UnitOfMeasureModel, uom_id) is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Unit of measure was not found.",
        )


def _validate_vat_rate(session: Session, vat_rate_id: uuid.UUID | None) -> None:
    if vat_rate_id is None:
        return
    if session.get(VatRateModel, vat_rate_id) is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="VAT rate was not found.",
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


def _decimal_or_none(value: Any) -> Decimal | None:
    return Decimal(value) if value is not None else None
