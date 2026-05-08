"""Estimated stock side effects for accepted POS sale lines."""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, time
from decimal import Decimal
from typing import Any, Mapping

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.inventory.infrastructure.orm.estimated_consumption_model import (
    EstimatedConsumptionAuditModel,
)
from app.modules.inventory.infrastructure.orm.inventory_item_model import (
    InventoryItemModel,
)
from app.modules.master_data.infrastructure.orm.product_model import ProductModel
from app.modules.master_data.infrastructure.orm.unit_of_measure_model import (
    UnitOfMeasureModel,
)
from app.modules.pos_ingestion.infrastructure.orm.pos_product_alias_model import (
    PosProductAliasModel,
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
        source_type: str,
        source_id: uuid.UUID,
        occurred_at: datetime | None = None,
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
                business_unit_id=business_unit_id,
                product=product,
                recipe_version=recipe_version,
                sold_quantity=sold_quantity,
                payload=payload,
                source_type=source_type,
                source_id=source_id,
                occurred_at=occurred_at or _extract_occurred_at(payload),
            )
            return

        self._consume_direct_stock(
            product=product,
            sold_quantity=sold_quantity,
            payload=payload,
            source_type=source_type,
            source_id=source_id,
            occurred_at=occurred_at or _extract_occurred_at(payload),
        )

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

        alias_product = self._resolve_mapped_alias_product(
            business_unit_id=business_unit_id,
            payload=payload,
        )
        if alias_product is not None:
            return alias_product

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

    def _resolve_mapped_alias_product(
        self,
        *,
        business_unit_id: uuid.UUID,
        payload: Mapping[str, Any],
    ) -> ProductModel | None:
        product_name = _optional_text(payload.get("product_name"))
        if product_name is None:
            return None

        source_system = _source_system(payload)
        source_product_key = _source_product_key(payload, product_name)
        alias = self._session.scalar(
            select(PosProductAliasModel)
            .where(PosProductAliasModel.business_unit_id == business_unit_id)
            .where(PosProductAliasModel.source_system == source_system)
            .where(PosProductAliasModel.source_product_key == source_product_key)
            .where(PosProductAliasModel.status == "mapped")
            .where(PosProductAliasModel.product_id.is_not(None))
            .limit(1)
        )
        if alias is None or alias.product_id is None:
            return None

        product = self._session.get(ProductModel, alias.product_id)
        if product is None or product.business_unit_id != business_unit_id:
            return None
        return product

    def _consume_recipe_stock(
        self,
        *,
        business_unit_id: uuid.UUID,
        product: ProductModel,
        recipe_version: RecipeVersionModel,
        sold_quantity: Decimal,
        payload: Mapping[str, Any],
        source_type: str,
        source_id: uuid.UUID,
        occurred_at: datetime,
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
                before, after = self._decrease_estimated_stock(item, converted_quantity)
                self._add_audit_row(
                    business_unit_id=business_unit_id,
                    product_id=product.id,
                    inventory_item_id=item.id,
                    recipe_version_id=recipe_version.id,
                    source_type=source_type,
                    source_id=source_id,
                    source_dedupe_key=_optional_text(payload.get("dedupe_key")),
                    receipt_no=_optional_text(payload.get("receipt_no")),
                    estimation_basis="recipe",
                    quantity=converted_quantity,
                    uom_id=item.uom_id,
                    quantity_before=before,
                    quantity_after=after,
                    occurred_at=occurred_at,
                )

    def _consume_direct_stock(
        self,
        *,
        product: ProductModel,
        sold_quantity: Decimal,
        payload: Mapping[str, Any],
        source_type: str,
        source_id: uuid.UUID,
        occurred_at: datetime,
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
            before, after = self._decrease_estimated_stock(item, converted_quantity)
            self._add_audit_row(
                business_unit_id=product.business_unit_id,
                product_id=product.id,
                inventory_item_id=item.id,
                recipe_version_id=None,
                source_type=source_type,
                source_id=source_id,
                source_dedupe_key=_optional_text(payload.get("dedupe_key")),
                receipt_no=_optional_text(payload.get("receipt_no")),
                estimation_basis="direct_product",
                quantity=converted_quantity,
                uom_id=item.uom_id,
                quantity_before=before,
                quantity_after=after,
                occurred_at=occurred_at,
            )

    @staticmethod
    def _decrease_estimated_stock(
        item: InventoryItemModel,
        quantity: Decimal,
    ) -> tuple[Decimal, Decimal]:
        current_quantity = Decimal(item.estimated_stock_quantity or 0)
        item.estimated_stock_quantity = max(
            Decimal("0"),
            current_quantity - quantity,
        ).quantize(Decimal("0.001"))
        return current_quantity.quantize(Decimal("0.001")), Decimal(
            item.estimated_stock_quantity
        )

    def _add_audit_row(
        self,
        *,
        business_unit_id: uuid.UUID,
        product_id: uuid.UUID,
        inventory_item_id: uuid.UUID,
        recipe_version_id: uuid.UUID | None,
        source_type: str,
        source_id: uuid.UUID,
        source_dedupe_key: str | None,
        receipt_no: str | None,
        estimation_basis: str,
        quantity: Decimal,
        uom_id: uuid.UUID,
        quantity_before: Decimal,
        quantity_after: Decimal,
        occurred_at: datetime,
    ) -> None:
        self._session.add(
            EstimatedConsumptionAuditModel(
                business_unit_id=business_unit_id,
                product_id=product_id,
                inventory_item_id=inventory_item_id,
                recipe_version_id=recipe_version_id,
                source_type=source_type,
                source_id=source_id,
                source_dedupe_key=source_dedupe_key,
                receipt_no=receipt_no,
                estimation_basis=estimation_basis,
                quantity=quantity.quantize(Decimal("0.001")),
                uom_id=uom_id,
                quantity_before=quantity_before,
                quantity_after=quantity_after,
                occurred_at=occurred_at,
            )
        )

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


def _optional_text(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped or None


def _source_system(payload: Mapping[str, Any]) -> str:
    source_import_profile = _optional_text(payload.get("source_import_profile"))
    return source_import_profile or "pos_sales"


def _source_product_key(payload: Mapping[str, Any], product_name: str) -> str:
    source_product_id = _optional_text(
        payload.get("source_product_id") or payload.get("pos_product_id")
    )
    if source_product_id is not None:
        return f"id:{source_product_id.casefold()}"

    source_sku = _optional_text(payload.get("sku"))
    if source_sku is not None:
        return f"sku:{source_sku.casefold()}"

    source_barcode = _optional_text(payload.get("barcode"))
    if source_barcode is not None:
        return f"barcode:{source_barcode.casefold()}"

    return f"name:{product_name.casefold()}"


def _extract_occurred_at(payload: Mapping[str, Any]) -> datetime:
    occurred_at = payload.get("occurred_at")
    if isinstance(occurred_at, str) and occurred_at:
        try:
            parsed = datetime.fromisoformat(occurred_at)
            if parsed.tzinfo is None:
                return parsed.replace(tzinfo=UTC)
            return parsed
        except ValueError:
            pass

    value = payload.get("date")
    if isinstance(value, str) and value:
        try:
            return datetime.combine(date.fromisoformat(value), time.min, tzinfo=UTC)
        except ValueError:
            pass

    return datetime.now(UTC)
