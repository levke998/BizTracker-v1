"""Catalog costing and inventory risk analytics queries."""

from __future__ import annotations

import uuid
from collections import defaultdict
from datetime import datetime
from decimal import Decimal

import sqlalchemy as sa
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.analytics.domain.entities.dashboard_snapshot import (
    DashboardProductRiskRow,
    DashboardStockRiskRow,
)
from app.modules.inventory.infrastructure.orm.inventory_item_model import (
    InventoryItemModel,
)
from app.modules.inventory.infrastructure.orm.inventory_movement_model import (
    InventoryMovementModel,
)
from app.modules.master_data.infrastructure.orm.category_model import CategoryModel
from app.modules.master_data.infrastructure.orm.product_model import ProductModel
from app.modules.master_data.infrastructure.orm.unit_of_measure_model import (
    UnitOfMeasureModel,
)
from app.modules.procurement.infrastructure.orm.purchase_invoice_line_model import (
    PurchaseInvoiceLineModel,
)
from app.modules.procurement.infrastructure.orm.purchase_invoice_model import (
    PurchaseInvoiceModel,
)
from app.modules.production.infrastructure.orm.recipe_model import (
    RecipeIngredientModel,
    RecipeModel,
    RecipeVersionModel,
)


class CatalogInventoryRiskReader:
    """Provide shared costing, stock summaries and risk read models."""

    def __init__(self, session: Session, *, unknown_category: str) -> None:
        self._session = session
        self._unknown_category = unknown_category

    def product_unit_costs(
        self,
        *,
        business_unit_id: uuid.UUID | None,
    ) -> dict[str, Decimal]:
        statement = (
            select(ProductModel, UnitOfMeasureModel.code)
            .outerjoin(
                UnitOfMeasureModel,
                ProductModel.sales_uom_id == UnitOfMeasureModel.id,
            )
            .where(ProductModel.is_active.is_(True))
        )
        if business_unit_id is not None:
            statement = statement.where(
                ProductModel.business_unit_id == business_unit_id
            )
        recipe_costs = self._recipe_product_unit_costs(
            self._latest_inventory_item_costs()
        )
        costs: dict[str, Decimal] = {}
        for product, sales_uom_code in self._session.execute(statement).all():
            unit_cost = recipe_costs.get(product.id)
            if unit_cost is None and product.default_unit_cost is not None:
                unit_cost = Decimal(product.default_unit_cost)
            if unit_cost is None:
                continue
            for key in (str(product.id), product.sku, product.name):
                if key:
                    costs[str(key)] = unit_cost
            if sales_uom_code:
                costs[f"{product.name}|{sales_uom_code}"] = unit_cost
        return costs

    def active_recipe_ingredients(
        self,
        *,
        business_unit_id: uuid.UUID | None,
    ) -> dict[uuid.UUID, list[RecipeIngredientModel]]:
        statement = (
            select(RecipeModel.product_id, RecipeIngredientModel)
            .join(RecipeVersionModel, RecipeVersionModel.recipe_id == RecipeModel.id)
            .outerjoin(
                RecipeIngredientModel,
                RecipeIngredientModel.recipe_version_id == RecipeVersionModel.id,
            )
            .join(ProductModel, ProductModel.id == RecipeModel.product_id)
            .where(RecipeModel.is_active.is_(True))
            .where(RecipeVersionModel.is_active.is_(True))
            .where(ProductModel.is_active.is_(True))
        )
        if business_unit_id is not None:
            statement = statement.where(
                ProductModel.business_unit_id == business_unit_id
            )
        result: dict[uuid.UUID, list[RecipeIngredientModel]] = defaultdict(list)
        for product_id, ingredient in self._session.execute(statement).all():
            if ingredient is not None:
                result[product_id].append(ingredient)
            else:
                result.setdefault(product_id, [])
        return dict(result)

    def stock_levels(
        self,
        *,
        business_unit_id: uuid.UUID | None,
    ) -> dict[uuid.UUID, dict[str, Decimal | int | datetime | None]]:
        signed_quantity = sa.case(
            (
                InventoryMovementModel.movement_type.in_(
                    ["purchase", "initial_stock", "adjustment"]
                ),
                InventoryMovementModel.quantity,
            ),
            (
                InventoryMovementModel.movement_type == "waste",
                -InventoryMovementModel.quantity,
            ),
            else_=0,
        )
        statement = (
            select(
                InventoryItemModel.id,
                sa.func.coalesce(sa.func.sum(signed_quantity), 0),
                sa.func.count(InventoryMovementModel.id),
                sa.func.max(InventoryMovementModel.occurred_at),
            )
            .select_from(InventoryItemModel)
            .outerjoin(
                InventoryMovementModel,
                InventoryMovementModel.inventory_item_id == InventoryItemModel.id,
            )
            .where(InventoryItemModel.is_active.is_(True))
            .group_by(InventoryItemModel.id)
        )
        if business_unit_id is not None:
            statement = statement.where(
                InventoryItemModel.business_unit_id == business_unit_id
            )
        return {
            item_id: {
                "current_quantity": Decimal(quantity),
                "movement_count": int(count),
                "last_movement_at": last_movement,
            }
            for item_id, quantity, count, last_movement in self._session.execute(
                statement
            ).all()
        }

    def build_product_risks(
        self,
        *,
        business_unit_id: uuid.UUID | None,
        limit: int,
    ) -> list[DashboardProductRiskRow]:
        statement = (
            select(ProductModel, CategoryModel.name)
            .outerjoin(CategoryModel, ProductModel.category_id == CategoryModel.id)
            .where(ProductModel.is_active.is_(True))
            .order_by(ProductModel.name.asc())
        )
        if business_unit_id is not None:
            statement = statement.where(
                ProductModel.business_unit_id == business_unit_id
            )
        recipe_costs = self._recipe_product_unit_costs(
            self._latest_inventory_item_costs()
        )
        ingredients = self.active_recipe_ingredients(
            business_unit_id=business_unit_id
        )
        stock = self.stock_levels(business_unit_id=business_unit_id)
        risks: list[tuple[int, DashboardProductRiskRow]] = []
        for product, category_name in self._session.execute(statement).all():
            sale_price = Decimal(product.sale_price_gross or 0)
            unit_cost = recipe_costs.get(product.id)
            if unit_cost is None and product.default_unit_cost is not None:
                unit_cost = Decimal(product.default_unit_cost)
            unit_cost = unit_cost or Decimal("0")
            margin = sale_price - unit_cost
            margin_percent = (
                margin / sale_price * Decimal("100")
                if sale_price > Decimal("0")
                else Decimal("0")
            )
            product_ingredients = ingredients.get(product.id, [])
            low_stock, missing_stock = self._ingredient_stock_risks(
                product_ingredients,
                stock,
            )
            reasons: list[str] = []
            score = 0
            if margin < Decimal("0"):
                reasons.append("Negatív árrés")
                score += 100
            elif Decimal("0") < margin_percent < Decimal("15"):
                reasons.append("Alacsony árrés")
                score += 45
            if product.sale_price_gross is None:
                reasons.append("Hiányzó eladási ár")
                score += 60
            if product.id in recipe_costs and not product_ingredients:
                reasons.append("Hiányzó receptsor")
                score += 55
            elif product.default_unit_cost is None and product.id not in recipe_costs:
                reasons.append("Hiányzó költségalap")
                score += 50
            if low_stock:
                reasons.append("Alapanyaghiány")
                score += 80 + low_stock * 5
            if missing_stock:
                reasons.append("Hiányzó készletadat")
                score += 35 + missing_stock * 3
            if not reasons:
                continue
            risks.append(
                (
                    score,
                    DashboardProductRiskRow(
                        product_id=product.id,
                        product_name=product.name,
                        category_name=category_name or self._unknown_category,
                        sale_price_gross=sale_price,
                        estimated_unit_cost=unit_cost,
                        estimated_margin_amount=margin,
                        estimated_margin_percent=margin_percent,
                        risk_level="danger" if score >= 80 else "warning",
                        risk_reasons=tuple(reasons),
                        low_stock_ingredient_count=low_stock,
                        missing_stock_ingredient_count=missing_stock,
                        source_layer="catalog_inventory_actual",
                    ),
                )
            )
        return [
            row
            for _score, row in sorted(
                risks,
                key=lambda item: (
                    item[0],
                    abs(item[1].estimated_margin_amount),
                    item[1].product_name,
                ),
                reverse=True,
            )[:limit]
        ]

    def build_stock_risks(
        self,
        *,
        business_unit_id: uuid.UUID | None,
        limit: int,
    ) -> list[DashboardStockRiskRow]:
        stock = self.stock_levels(business_unit_id=business_unit_id)
        usage = self._inventory_item_usage_counts(
            business_unit_id=business_unit_id
        )
        statement = (
            select(InventoryItemModel)
            .where(InventoryItemModel.is_active.is_(True))
            .where(InventoryItemModel.track_stock.is_(True))
            .order_by(InventoryItemModel.name.asc())
        )
        if business_unit_id is not None:
            statement = statement.where(
                InventoryItemModel.business_unit_id == business_unit_id
            )
        risks: list[tuple[int, DashboardStockRiskRow]] = []
        for item in self._session.scalars(statement).all():
            level = stock.get(item.id)
            current = (
                Decimal(level["current_quantity"]) if level else Decimal("0")
            )
            movement_count = int(level["movement_count"]) if level else 0
            used_by = usage.get(item.id, 0)
            reasons, score = self._stock_risk_score(
                item=item,
                current=current,
                movement_count=movement_count,
                used_by=used_by,
            )
            if not reasons:
                continue
            risks.append(
                (
                    score,
                    DashboardStockRiskRow(
                        inventory_item_id=item.id,
                        item_name=item.name,
                        item_type=item.item_type,
                        current_quantity=current,
                        theoretical_quantity=None,
                        variance_quantity=None,
                        used_by_product_count=used_by,
                        movement_count=movement_count,
                        last_movement_at=level["last_movement_at"] if level else None,
                        risk_level="danger" if score >= 80 else "warning",
                        risk_reasons=tuple(reasons),
                        source_layer="inventory_actual",
                    ),
                )
            )
        return [
            row
            for _score, row in sorted(
                risks,
                key=lambda item: (
                    item[0],
                    item[1].used_by_product_count,
                    item[1].item_name,
                ),
                reverse=True,
            )[:limit]
        ]

    def _latest_inventory_item_costs(self) -> dict[uuid.UUID, Decimal]:
        costs = {
            item.id: Decimal(item.default_unit_cost)
            for item in self._session.scalars(select(InventoryItemModel)).all()
            if item.default_unit_cost is not None
        }
        rows = self._session.execute(
            select(PurchaseInvoiceLineModel, PurchaseInvoiceModel.invoice_date)
            .join(
                PurchaseInvoiceModel,
                PurchaseInvoiceModel.id == PurchaseInvoiceLineModel.invoice_id,
            )
            .where(PurchaseInvoiceLineModel.inventory_item_id.is_not(None))
            .order_by(
                PurchaseInvoiceModel.invoice_date.asc(),
                PurchaseInvoiceLineModel.id.asc(),
            )
        ).all()
        for line, _invoice_date in rows:
            if line.inventory_item_id is not None:
                costs[line.inventory_item_id] = Decimal(line.unit_net_amount)
        return costs

    def _recipe_product_unit_costs(
        self,
        item_costs: dict[uuid.UUID, Decimal],
    ) -> dict[uuid.UUID, Decimal]:
        uom_codes = {
            unit.id: unit.code
            for unit in self._session.scalars(select(UnitOfMeasureModel)).all()
        }
        versions = self._session.execute(
            select(
                RecipeModel.product_id,
                RecipeVersionModel.id,
                RecipeVersionModel.yield_quantity,
            )
            .join(RecipeVersionModel, RecipeVersionModel.recipe_id == RecipeModel.id)
            .where(RecipeModel.is_active.is_(True))
            .where(RecipeVersionModel.is_active.is_(True))
        ).all()
        costs: dict[uuid.UUID, Decimal] = {}
        for product_id, version_id, yield_quantity in versions:
            ingredients = self._session.execute(
                select(RecipeIngredientModel, InventoryItemModel.uom_id)
                .join(
                    InventoryItemModel,
                    InventoryItemModel.id == RecipeIngredientModel.inventory_item_id,
                )
                .where(RecipeIngredientModel.recipe_version_id == version_id)
            ).all()
            total = Decimal("0")
            for ingredient, item_uom_id in ingredients:
                unit_cost = item_costs.get(ingredient.inventory_item_id)
                if unit_cost is None:
                    continue
                total += self._convert_quantity(
                    Decimal(ingredient.quantity),
                    from_uom=uom_codes.get(ingredient.uom_id),
                    to_uom=uom_codes.get(item_uom_id),
                ) * unit_cost
            yield_qty = Decimal(yield_quantity)
            if yield_qty > 0:
                costs[product_id] = total / yield_qty
        return costs

    def _inventory_item_usage_counts(
        self,
        *,
        business_unit_id: uuid.UUID | None,
    ) -> dict[uuid.UUID, int]:
        statement = (
            select(
                RecipeIngredientModel.inventory_item_id,
                sa.func.count(sa.func.distinct(ProductModel.id)),
            )
            .join(
                RecipeVersionModel,
                RecipeVersionModel.id == RecipeIngredientModel.recipe_version_id,
            )
            .join(RecipeModel, RecipeModel.id == RecipeVersionModel.recipe_id)
            .join(ProductModel, ProductModel.id == RecipeModel.product_id)
            .where(RecipeModel.is_active.is_(True))
            .where(RecipeVersionModel.is_active.is_(True))
            .where(ProductModel.is_active.is_(True))
            .group_by(RecipeIngredientModel.inventory_item_id)
        )
        if business_unit_id is not None:
            statement = statement.where(
                ProductModel.business_unit_id == business_unit_id
            )
        return {
            item_id: int(count)
            for item_id, count in self._session.execute(statement).all()
        }

    @staticmethod
    def _ingredient_stock_risks(
        ingredients: list[RecipeIngredientModel],
        stock: dict[uuid.UUID, dict[str, Decimal | int | datetime | None]],
    ) -> tuple[int, int]:
        low = 0
        missing = 0
        for ingredient in ingredients:
            level = stock.get(ingredient.inventory_item_id)
            if level is None or int(level["movement_count"]) == 0:
                missing += 1
            elif Decimal(level["current_quantity"]) <= Decimal("0"):
                low += 1
        return low, missing

    @staticmethod
    def _stock_risk_score(
        *,
        item: InventoryItemModel,
        current: Decimal,
        movement_count: int,
        used_by: int,
    ) -> tuple[list[str], int]:
        reasons: list[str] = []
        score = 0
        if movement_count == 0:
            reasons.append("Nincs készletmozgás")
            score += 55
        if current <= Decimal("0"):
            reasons.append("Nincs tényleges készlet")
            score += 90
        elif used_by > 0 and current <= Decimal(used_by):
            reasons.append("Alacsony készlet recept-használathoz képest")
            score += 45
        if item.estimated_stock_quantity is None:
            reasons.append("Hiányzó becsült készlet")
            score += 25
        elif Decimal(item.estimated_stock_quantity) <= Decimal("0"):
            reasons.append("Becsült készlet nulla")
            score += 35
        if used_by > 0:
            score += min(used_by * 4, 24)
        return reasons, score

    @staticmethod
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
        source = factors.get(from_uom)
        target = factors.get(to_uom)
        if source is None or target is None or source[0] != target[0]:
            return quantity
        return quantity * source[1] / target[1]
