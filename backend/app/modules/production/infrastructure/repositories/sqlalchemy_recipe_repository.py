"""SQLAlchemy implementation for production recipe read models."""

from __future__ import annotations

from decimal import Decimal
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.finance.application.services.vat_calculator import VatCalculator
from app.modules.inventory.infrastructure.orm.inventory_item_model import (
    InventoryItemModel,
)
from app.modules.master_data.infrastructure.orm.category_model import CategoryModel
from app.modules.master_data.infrastructure.orm.product_model import ProductModel
from app.modules.master_data.infrastructure.orm.unit_of_measure_model import (
    UnitOfMeasureModel,
)
from app.modules.master_data.infrastructure.orm.vat_rate_model import VatRateModel
from app.modules.production.domain.entities.recipe import (
    IngredientStockStatus,
    RecipeCostStatus,
    RecipeCostSummary,
    RecipeDraft,
    RecipeIngredientCost,
    RecipeReadinessStatus,
)
from app.modules.production.infrastructure.orm.recipe_model import (
    RecipeIngredientModel,
    RecipeModel,
    RecipeVersionModel,
)


class SqlAlchemyRecipeRepository:
    """Build production recipe costing/readiness read models from ORM data."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def list_recipe_summaries(
        self,
        *,
        business_unit_id: uuid.UUID,
        product_id: uuid.UUID | None = None,
        active_only: bool = True,
    ) -> list[RecipeCostSummary]:
        """Return one row per product, including products without recipes."""

        product_rows = self._load_products(
            business_unit_id=business_unit_id,
            product_id=product_id,
            active_only=active_only,
        )
        product_ids = [product.id for product, _category_name in product_rows]
        if not product_ids:
            return []

        latest_recipe_by_product = self._load_active_recipe_versions(product_ids=product_ids)
        ingredients_by_version = self._load_ingredients(
            version_ids=[
                version.id
                for _recipe, version, _yield_uom_code in latest_recipe_by_product.values()
            ]
        )

        summaries: list[RecipeCostSummary] = []
        for product, category_name in product_rows:
            recipe_tuple = latest_recipe_by_product.get(product.id)
            if recipe_tuple is None:
                summaries.append(
                    RecipeCostSummary(
                        product_id=product.id,
                        business_unit_id=product.business_unit_id,
                        product_name=product.name,
                        category_name=category_name,
                        recipe_id=None,
                        recipe_name=None,
                        version_id=None,
                        version_no=None,
                        yield_quantity=None,
                        yield_uom_id=None,
                        yield_uom_code=None,
                        known_total_cost=Decimal("0"),
                        total_cost=None,
                        unit_cost=None,
                        cost_status=RecipeCostStatus.NO_RECIPE,
                        readiness_status=RecipeReadinessStatus.MISSING_RECIPE,
                        warnings=("missing_recipe",),
                        ingredients=(),
                    )
                )
                continue

            recipe, version, yield_uom_code = recipe_tuple
            ingredients = tuple(ingredients_by_version.get(version.id, ()))
            summaries.append(
                self._build_recipe_summary(
                    product=product,
                    category_name=category_name,
                    recipe=recipe,
                    version=version,
                    yield_uom_code=yield_uom_code,
                    ingredients=ingredients,
                )
            )

        return summaries

    def unit_exists(self, uom_id: uuid.UUID) -> bool:
        """Return whether a unit of measure exists."""

        return self._session.get(UnitOfMeasureModel, uom_id) is not None

    def inventory_item_belongs_to_business_unit(
        self,
        *,
        inventory_item_id: uuid.UUID,
        business_unit_id: uuid.UUID,
    ) -> bool:
        """Return whether an inventory item belongs to the business unit."""

        item = self._session.get(InventoryItemModel, inventory_item_id)
        return item is not None and item.business_unit_id == business_unit_id

    def save_active_recipe(
        self,
        *,
        product_id: uuid.UUID,
        draft: RecipeDraft,
    ) -> None:
        """Create a new active version and deactivate previous active versions."""

        recipe = self._session.scalar(
            select(RecipeModel)
            .where(RecipeModel.product_id == product_id)
            .where(RecipeModel.is_active.is_(True))
            .order_by(RecipeModel.created_at.asc())
        )
        if recipe is None:
            recipe = RecipeModel(
                product_id=product_id,
                name=draft.name.strip(),
                is_active=True,
            )
            self._session.add(recipe)
            self._session.flush()
        else:
            recipe.name = draft.name.strip()

        latest_version_no = self._session.scalar(
            select(RecipeVersionModel.version_no)
            .where(RecipeVersionModel.recipe_id == recipe.id)
            .order_by(RecipeVersionModel.version_no.desc())
            .limit(1)
        )
        active_versions = self._session.scalars(
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
            yield_quantity=draft.yield_quantity,
            yield_uom_id=draft.yield_uom_id,
            notes="Catalog edit",
        )
        self._session.add(version)
        self._session.flush()

        for ingredient in draft.ingredients:
            self._session.add(
                RecipeIngredientModel(
                    recipe_version_id=version.id,
                    inventory_item_id=ingredient.inventory_item_id,
                    quantity=ingredient.quantity,
                    uom_id=ingredient.uom_id,
                )
            )

    def _load_products(
        self,
        *,
        business_unit_id: uuid.UUID,
        product_id: uuid.UUID | None,
        active_only: bool,
    ) -> list[tuple[ProductModel, str | None]]:
        statement = (
            select(ProductModel, CategoryModel.name)
            .outerjoin(CategoryModel, ProductModel.category_id == CategoryModel.id)
            .where(ProductModel.business_unit_id == business_unit_id)
            .order_by(CategoryModel.name.asc().nulls_last(), ProductModel.name.asc())
        )
        if product_id is not None:
            statement = statement.where(ProductModel.id == product_id)
        if active_only:
            statement = statement.where(ProductModel.is_active.is_(True))
        return list(self._session.execute(statement).all())

    def _load_active_recipe_versions(
        self,
        *,
        product_ids: list[uuid.UUID],
    ) -> dict[uuid.UUID, tuple[RecipeModel, RecipeVersionModel, str | None]]:
        if not product_ids:
            return {}

        rows = self._session.execute(
            select(RecipeModel, RecipeVersionModel, UnitOfMeasureModel.code)
            .join(RecipeVersionModel, RecipeVersionModel.recipe_id == RecipeModel.id)
            .outerjoin(UnitOfMeasureModel, RecipeVersionModel.yield_uom_id == UnitOfMeasureModel.id)
            .where(RecipeModel.product_id.in_(product_ids))
            .where(RecipeModel.is_active.is_(True))
            .where(RecipeVersionModel.is_active.is_(True))
            .order_by(RecipeModel.product_id.asc(), RecipeVersionModel.version_no.desc())
        ).all()

        latest_by_product: dict[uuid.UUID, tuple[RecipeModel, RecipeVersionModel, str | None]] = {}
        for recipe, version, yield_uom_code in rows:
            latest_by_product.setdefault(recipe.product_id, (recipe, version, yield_uom_code))
        return latest_by_product

    def _load_ingredients(
        self,
        *,
        version_ids: list[uuid.UUID],
    ) -> dict[uuid.UUID, list[RecipeIngredientCost]]:
        if not version_ids:
            return {}

        rows = self._session.execute(
            select(
                RecipeIngredientModel,
                InventoryItemModel.name,
                InventoryItemModel.default_unit_cost,
                InventoryItemModel.default_vat_rate_id,
                VatRateModel.rate_percent,
                InventoryItemModel.estimated_stock_quantity,
                InventoryItemModel.track_stock,
                ingredient_uom_alias.c.code,
                item_uom_alias.c.code,
            )
            .join(InventoryItemModel, RecipeIngredientModel.inventory_item_id == InventoryItemModel.id)
            .outerjoin(VatRateModel, InventoryItemModel.default_vat_rate_id == VatRateModel.id)
            .outerjoin(
                ingredient_uom_alias,
                RecipeIngredientModel.uom_id == ingredient_uom_alias.c.id,
            )
            .outerjoin(item_uom_alias, InventoryItemModel.uom_id == item_uom_alias.c.id)
            .where(RecipeIngredientModel.recipe_version_id.in_(version_ids))
            .order_by(InventoryItemModel.name.asc())
        ).all()

        by_version: dict[uuid.UUID, list[RecipeIngredientCost]] = {}
        for (
            ingredient,
            item_name,
            default_unit_cost,
            default_vat_rate_id,
            vat_rate_percent,
            estimated_stock_quantity,
            track_stock,
            ingredient_uom_code,
            item_uom_code,
        ) in rows:
            converted_quantity = _convert_quantity(
                Decimal(ingredient.quantity),
                from_uom=ingredient_uom_code,
                to_uom=item_uom_code,
            )
            unit_cost = _decimal_or_none(default_unit_cost)
            estimated_cost = (
                converted_quantity * unit_cost if unit_cost is not None else None
            )
            tax_amount, gross_cost = _tax_from_net(
                estimated_cost=estimated_cost,
                vat_rate_percent=_decimal_or_none(vat_rate_percent),
            )
            stock_quantity = _decimal_or_none(estimated_stock_quantity)
            by_version.setdefault(ingredient.recipe_version_id, []).append(
                RecipeIngredientCost(
                    inventory_item_id=ingredient.inventory_item_id,
                    inventory_item_name=item_name,
                    quantity=Decimal(ingredient.quantity),
                    uom_id=ingredient.uom_id,
                    uom_code=ingredient_uom_code,
                    item_uom_code=item_uom_code,
                    converted_quantity=converted_quantity,
                    unit_cost=unit_cost,
                    estimated_cost=estimated_cost,
                    estimated_stock_quantity=stock_quantity,
                    track_stock=bool(track_stock),
                    stock_status=_stock_status(
                        converted_quantity=converted_quantity,
                        stock_quantity=stock_quantity,
                        track_stock=bool(track_stock),
                    ),
                    default_vat_rate_id=default_vat_rate_id,
                    vat_rate_percent=_decimal_or_none(vat_rate_percent),
                    estimated_vat_amount=tax_amount,
                    estimated_gross_cost=gross_cost,
                )
            )

        return by_version

    def _build_recipe_summary(
        self,
        *,
        product: ProductModel,
        category_name: str | None,
        recipe: RecipeModel,
        version: RecipeVersionModel,
        yield_uom_code: str | None,
        ingredients: tuple[RecipeIngredientCost, ...],
    ) -> RecipeCostSummary:
        if not ingredients:
            return RecipeCostSummary(
                product_id=product.id,
                business_unit_id=product.business_unit_id,
                product_name=product.name,
                category_name=category_name,
                recipe_id=recipe.id,
                recipe_name=recipe.name,
                version_id=version.id,
                version_no=version.version_no,
                yield_quantity=Decimal(version.yield_quantity),
                yield_uom_id=version.yield_uom_id,
                yield_uom_code=yield_uom_code,
                known_total_cost=Decimal("0"),
                total_cost=None,
                unit_cost=None,
                cost_status=RecipeCostStatus.EMPTY_RECIPE,
                readiness_status=RecipeReadinessStatus.EMPTY_RECIPE,
                warnings=("empty_recipe",),
                ingredients=ingredients,
            )

        known_total_cost = sum(
            (
                ingredient.estimated_cost
                for ingredient in ingredients
                if ingredient.estimated_cost is not None
            ),
            Decimal("0"),
        )
        missing_cost = any(ingredient.estimated_cost is None for ingredient in ingredients)
        missing_vat_rate = any(
            ingredient.estimated_cost is not None and ingredient.vat_rate_percent is None
            for ingredient in ingredients
        )
        stock_warning = any(
            ingredient.stock_status
            in (IngredientStockStatus.MISSING, IngredientStockStatus.INSUFFICIENT)
            for ingredient in ingredients
        )

        cost_status = (
            RecipeCostStatus.MISSING_COST if missing_cost else RecipeCostStatus.COMPLETE
        )
        total_cost = None if missing_cost else known_total_cost
        known_total_vat_amount = sum(
            (
                ingredient.estimated_vat_amount
                for ingredient in ingredients
                if ingredient.estimated_vat_amount is not None
            ),
            Decimal("0"),
        )
        known_total_gross_cost = sum(
            (
                ingredient.estimated_gross_cost
                for ingredient in ingredients
                if ingredient.estimated_gross_cost is not None
            ),
            Decimal("0"),
        )
        total_vat_amount = None if missing_cost or missing_vat_rate else known_total_vat_amount
        total_gross_cost = None if missing_cost or missing_vat_rate else known_total_gross_cost
        yield_quantity = Decimal(version.yield_quantity)
        unit_cost = (
            total_cost / yield_quantity
            if total_cost is not None and yield_quantity > 0
            else None
        )
        unit_gross_cost = (
            total_gross_cost / yield_quantity
            if total_gross_cost is not None and yield_quantity > 0
            else None
        )
        readiness_status = _readiness_status(
            cost_status=cost_status,
            has_stock_warning=stock_warning,
        )
        warnings = _warnings(
            missing_cost=missing_cost,
            missing_vat_rate=missing_vat_rate,
            stock_warning=stock_warning,
        )

        return RecipeCostSummary(
            product_id=product.id,
            business_unit_id=product.business_unit_id,
            product_name=product.name,
            category_name=category_name,
            recipe_id=recipe.id,
            recipe_name=recipe.name,
            version_id=version.id,
            version_no=version.version_no,
            yield_quantity=yield_quantity,
            yield_uom_id=version.yield_uom_id,
            yield_uom_code=yield_uom_code,
            known_total_cost=known_total_cost,
            total_cost=total_cost,
            unit_cost=unit_cost,
            cost_status=cost_status,
            readiness_status=readiness_status,
            warnings=warnings,
            ingredients=ingredients,
            known_total_vat_amount=known_total_vat_amount,
            total_vat_amount=total_vat_amount,
            known_total_gross_cost=known_total_gross_cost,
            total_gross_cost=total_gross_cost,
            unit_gross_cost=unit_gross_cost,
            tax_status=_tax_status(
                missing_cost=missing_cost,
                missing_vat_rate=missing_vat_rate,
            ),
        )


ingredient_uom_alias = UnitOfMeasureModel.__table__.alias("ingredient_uom")
item_uom_alias = UnitOfMeasureModel.__table__.alias("item_uom")


def _stock_status(
    *,
    converted_quantity: Decimal,
    stock_quantity: Decimal | None,
    track_stock: bool,
) -> IngredientStockStatus:
    if not track_stock:
        return IngredientStockStatus.NOT_TRACKED
    if stock_quantity is None:
        return IngredientStockStatus.UNKNOWN
    if stock_quantity <= 0:
        return IngredientStockStatus.MISSING
    if stock_quantity < converted_quantity:
        return IngredientStockStatus.INSUFFICIENT
    return IngredientStockStatus.OK


def _readiness_status(
    *,
    cost_status: RecipeCostStatus,
    has_stock_warning: bool,
) -> RecipeReadinessStatus:
    if cost_status == RecipeCostStatus.MISSING_COST:
        return RecipeReadinessStatus.MISSING_COST
    if has_stock_warning:
        return RecipeReadinessStatus.MISSING_STOCK
    return RecipeReadinessStatus.READY


def _warnings(
    *,
    missing_cost: bool,
    missing_vat_rate: bool,
    stock_warning: bool,
) -> tuple[str, ...]:
    warnings: list[str] = []
    if missing_cost:
        warnings.append("missing_cost")
    if missing_vat_rate:
        warnings.append("missing_vat_rate")
    if stock_warning:
        warnings.append("missing_stock")
    return tuple(warnings)


def _tax_status(*, missing_cost: bool, missing_vat_rate: bool) -> str:
    if missing_cost:
        return "incomplete_cost"
    if missing_vat_rate:
        return "missing_vat_rate"
    return "product_vat_derived"


def _tax_from_net(
    *,
    estimated_cost: Decimal | None,
    vat_rate_percent: Decimal | None,
) -> tuple[Decimal | None, Decimal | None]:
    if estimated_cost is None or vat_rate_percent is None:
        return None, None

    result = VatCalculator().calculate_from_net(
        net_amount=estimated_cost,
        rate_percent=vat_rate_percent,
    )
    return result.vat_amount, result.gross_amount


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


def _decimal_or_none(value: object) -> Decimal | None:
    return Decimal(value) if value is not None else None
