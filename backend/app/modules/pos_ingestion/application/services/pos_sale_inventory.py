"""Estimated stock side effects for accepted POS sale lines."""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any, Mapping

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.inventory.infrastructure.orm.inventory_item_model import (
    InventoryItemModel,
)
from app.modules.master_data.infrastructure.orm.product_model import ProductModel
from app.modules.master_data.infrastructure.orm.unit_of_measure_model import (
    UnitOfMeasureModel,
)
from app.modules.production.infrastructure.orm.recipe_model import (
    RecipeIngredientModel,
    RecipeModel,
    RecipeVersionModel,
)


class PosSaleInventoryConsumptionService:
    """Decrease estimated inventory for one accepted POS sale line."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def consume_line(
        self,
        *,
        business_unit_id: uuid.UUID,
        payload: Mapping[str, Any],
    ) -> None:
        product = self._resolve_product(
            business_unit_id=business_unit_id,
            payload=payload,
        )
        if product is None:
            return

        sold_quantity = _to_decimal(payload.get("quantity"))
        if sold_quantity <= 0:
            return

        recipe_version = self._session.scalar(
            select(RecipeVersionModel)
            .join(RecipeModel, RecipeModel.id == RecipeVersionModel.recipe_id)
            .where(RecipeModel.product_id == product.id)
            .where(RecipeModel.is_active.is_(True))
            .where(RecipeVersionModel.is_active.is_(True))
            .order_by(RecipeVersionModel.version_no.desc())
            .limit(1)
        )
        if recipe_version is not None:
            self._consume_recipe_stock(
                recipe_version=recipe_version,
                sold_quantity=sold_quantity,
            )
            return

        self._consume_direct_stock(product=product, sold_quantity=sold_quantity)

    def commit(self) -> None:
        """Commit inventory changes when the caller owns no broader transaction."""

        self._session.commit()

    def _resolve_product(
        self,
        *,
        business_unit_id: uuid.UUID,
        payload: Mapping[str, Any],
    ) -> ProductModel | None:
        product_id = payload.get("product_id")
        if isinstance(product_id, str):
            try:
                product = self._session.get(ProductModel, uuid.UUID(product_id))
            except ValueError:
                product = None
            if product is not None and product.business_unit_id == business_unit_id:
                return product

        sku = payload.get("sku")
        if isinstance(sku, str) and sku.strip():
            product = self._session.scalar(
                select(ProductModel)
                .where(ProductModel.business_unit_id == business_unit_id)
                .where(ProductModel.sku == sku.strip())
                .where(ProductModel.is_active.is_(True))
                .limit(1)
            )
            if product is not None:
                return product

        product_name = payload.get("product_name")
        if isinstance(product_name, str) and product_name.strip():
            return self._session.scalar(
                select(ProductModel)
                .where(ProductModel.business_unit_id == business_unit_id)
                .where(ProductModel.name == product_name.strip())
                .where(ProductModel.is_active.is_(True))
                .limit(1)
            )

        return None

    def _consume_recipe_stock(
        self,
        *,
        recipe_version: RecipeVersionModel,
        sold_quantity: Decimal,
    ) -> None:
        yield_quantity = Decimal(recipe_version.yield_quantity)
        if yield_quantity <= 0:
            return

        ingredients = self._session.scalars(
            select(RecipeIngredientModel).where(
                RecipeIngredientModel.recipe_version_id == recipe_version.id
            )
        ).all()
        for ingredient in ingredients:
            item = self._session.get(InventoryItemModel, ingredient.inventory_item_id)
            if item is None or item.estimated_stock_quantity is None:
                continue

            quantity = Decimal(ingredient.quantity) * sold_quantity / yield_quantity
            converted_quantity = self._convert_quantity(
                quantity,
                from_uom=self._get_uom_code(ingredient.uom_id),
                to_uom=self._get_uom_code(item.uom_id),
            )
            if converted_quantity is not None:
                self._decrease_estimated_stock(item, converted_quantity)

    def _consume_direct_stock(
        self,
        *,
        product: ProductModel,
        sold_quantity: Decimal,
    ) -> None:
        item = self._session.scalar(
            select(InventoryItemModel)
            .where(InventoryItemModel.business_unit_id == product.business_unit_id)
            .where(InventoryItemModel.name == product.name)
            .where(InventoryItemModel.track_stock.is_(True))
            .where(InventoryItemModel.is_active.is_(True))
            .limit(1)
        )
        if item is None or item.estimated_stock_quantity is None:
            return

        converted_quantity = self._convert_quantity(
            sold_quantity,
            from_uom=self._get_uom_code(product.sales_uom_id),
            to_uom=self._get_uom_code(item.uom_id),
        )
        if converted_quantity is not None:
            self._decrease_estimated_stock(item, converted_quantity)

    @staticmethod
    def _decrease_estimated_stock(
        item: InventoryItemModel,
        quantity: Decimal,
    ) -> None:
        current_quantity = Decimal(item.estimated_stock_quantity or 0)
        item.estimated_stock_quantity = max(
            Decimal("0"),
            current_quantity - quantity,
        ).quantize(Decimal("0.001"))

    def _get_uom_code(self, uom_id: uuid.UUID | None) -> str | None:
        if uom_id is None:
            return None
        unit = self._session.get(UnitOfMeasureModel, uom_id)
        return unit.code if unit else None

    @staticmethod
    def _convert_quantity(
        quantity: Decimal,
        *,
        from_uom: str | None,
        to_uom: str | None,
    ) -> Decimal | None:
        if from_uom == to_uom:
            return quantity
        if from_uom is None or to_uom is None:
            return None

        factors = {
            "g": ("mass", Decimal("0.001")),
            "kg": ("mass", Decimal("1")),
            "ml": ("volume", Decimal("0.001")),
            "l": ("volume", Decimal("1")),
        }
        from_factor = factors.get(from_uom)
        to_factor = factors.get(to_uom)
        if from_factor is None or to_factor is None or from_factor[0] != to_factor[0]:
            return None

        return (quantity * from_factor[1]) / to_factor[1]


def _to_decimal(value: Any) -> Decimal:
    if value is None:
        return Decimal("0")
    return Decimal(str(value))
