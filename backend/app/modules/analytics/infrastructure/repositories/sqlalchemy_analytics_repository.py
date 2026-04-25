"""SQLAlchemy analytics read-model repository."""

from __future__ import annotations

import uuid
from collections import defaultdict
from datetime import date, datetime, time
from decimal import Decimal, InvalidOperation
from itertools import combinations
from typing import Any
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.analytics.domain.entities.dashboard_snapshot import (
    DashboardBasketPairRow,
    DashboardBasketReceipt,
    DashboardBasketReceiptLine,
    DashboardBreakdownRow,
    DashboardExpenseDetailRow,
    DashboardExpenseRow,
    DashboardExpenseSource,
    DashboardExpenseSourceLine,
    DashboardKpi,
    DashboardPeriod,
    DashboardPosSourceRow,
    DashboardProductDetailRow,
    DashboardSnapshot,
    DashboardTrendPoint,
)
from app.modules.finance.infrastructure.orm.transaction_model import (
    FinancialTransactionModel,
)
from app.modules.imports.infrastructure.orm.import_batch_model import ImportBatchModel
from app.modules.imports.infrastructure.orm.import_row_model import ImportRowModel
from app.modules.inventory.infrastructure.orm.inventory_item_model import (
    InventoryItemModel,
)
from app.modules.master_data.infrastructure.orm.business_unit_model import (
    BusinessUnitModel,
)
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
from app.modules.procurement.infrastructure.orm.supplier_model import SupplierModel
from app.modules.production.infrastructure.orm.recipe_model import (
    RecipeIngredientModel,
    RecipeModel,
    RecipeVersionModel,
)

BUSINESS_SCOPE_CODES = {
    "flow": "flow",
    "gourmand": "gourmand",
}
UNKNOWN_CATEGORY = "Uncategorized"
UNKNOWN_PRODUCT = "Unknown product"
SUPPLIER_INVOICE_SOURCE_TYPE = "supplier_invoice"
APP_TIME_ZONE = ZoneInfo("Europe/Budapest")


class SqlAlchemyAnalyticsRepository:
    """Build dashboard read models from operational actuals and import rows."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_business_dashboard(
        self,
        *,
        scope: str,
        business_unit_id: uuid.UUID | None,
        preset: str,
        start_date: date,
        end_date: date,
        grain: str,
    ) -> DashboardSnapshot:
        resolved_business_unit_id, business_unit_name = self._resolve_business_unit(
            scope=scope,
            business_unit_id=business_unit_id,
        )
        transactions = self._list_financial_transactions(
            business_unit_id=resolved_business_unit_id,
            start_date=start_date,
            end_date=end_date,
        )
        import_rows = self._list_pos_sales_rows(
            business_unit_id=resolved_business_unit_id,
        )
        product_costs = self._build_product_unit_costs(
            business_unit_id=resolved_business_unit_id,
        )

        revenue = self._sum_transactions(transactions, direction="inflow")
        cost = self._sum_transactions(transactions, direction="outflow")
        profit = revenue - cost
        estimated_cogs = self._sum_estimated_cogs(
            rows=import_rows,
            product_costs=product_costs,
            start_date=start_date,
            end_date=end_date,
        )
        margin_profit = revenue - estimated_cogs
        transaction_count = len(transactions)
        profit_margin = (
            (margin_profit / revenue * Decimal("100"))
            if revenue > Decimal("0")
            else Decimal("0")
        )
        average_basket_value, average_basket_quantity = self._build_basket_metrics(
            rows=import_rows,
            start_date=start_date,
            end_date=end_date,
        )

        return DashboardSnapshot(
            scope=scope,
            business_unit_id=resolved_business_unit_id,
            business_unit_name=business_unit_name,
            period=DashboardPeriod(
                preset=preset,
                start_date=start_date,
                end_date=end_date,
                grain=grain,
            ),
            kpis=(
                DashboardKpi("revenue", "Revenue", revenue, "HUF", "financial_actual"),
                DashboardKpi("cost", "Cost", cost, "HUF", "financial_actual"),
                DashboardKpi("profit", "Profit", profit, "HUF", "derived_actual"),
                DashboardKpi(
                    "estimated_cogs",
                    "Estimated COGS",
                    estimated_cogs,
                    "HUF",
                    "recipe_or_unit_cost",
                ),
                DashboardKpi(
                    "transaction_count",
                    "Transactions",
                    Decimal(transaction_count),
                    "count",
                    "financial_actual",
                ),
                DashboardKpi(
                    "profit_margin",
                    "Profit margin",
                    margin_profit,
                    "HUF",
                    "recipe_or_unit_cost",
                ),
                DashboardKpi(
                    "gross_margin_percent",
                    "Gross margin %",
                    profit_margin,
                    "%",
                    "recipe_or_unit_cost",
                ),
                DashboardKpi(
                    "average_basket_value",
                    "Average basket value",
                    average_basket_value,
                    "HUF",
                    "import_derived",
                ),
                DashboardKpi(
                    "average_basket_quantity",
                    "Average basket quantity",
                    average_basket_quantity,
                    "count",
                    "import_derived",
                ),
            ),
            revenue_trend=tuple(
                self._build_trend(
                    transactions=transactions,
                    rows=import_rows,
                    product_costs=product_costs,
                    start_date=start_date,
                    end_date=end_date,
                    grain=grain,
                )
            ),
            category_breakdown=tuple(
                self._build_pos_breakdown(
                    rows=import_rows,
                    start_date=start_date,
                    end_date=end_date,
                    key_name="category_name",
                    fallback=UNKNOWN_CATEGORY,
                    limit=12,
                )
            ),
            top_products=tuple(
                self._build_pos_breakdown(
                    rows=import_rows,
                    start_date=start_date,
                    end_date=end_date,
                    key_name="product_name",
                    fallback=UNKNOWN_PRODUCT,
                    limit=10,
                )
            ),
            expense_breakdown=tuple(
                self._build_expense_breakdown(transactions=transactions, limit=10)
            ),
            notes=(
                "Financial KPIs are calculated from core.financial_transaction actuals.",
                "Cost is the actual posted outflow in the selected period; if no expense is posted for a day, cost is zero for that day.",
                "Product and category breakdowns are derived from parsed pos_sales import rows.",
                "Average basket KPIs are derived from pos_sales receipt_no groups.",
                "Profit uses revenue minus posted financial outflows; Profit margin uses estimated recipe or unit-cost COGS.",
            ),
        )

    def list_category_breakdown(
        self,
        *,
        scope: str,
        business_unit_id: uuid.UUID | None,
        start_date: date,
        end_date: date,
    ) -> list[DashboardBreakdownRow]:
        resolved_business_unit_id, _business_unit_name = self._resolve_business_unit(
            scope=scope,
            business_unit_id=business_unit_id,
        )
        return self._build_pos_breakdown(
            rows=self._list_pos_sales_rows(business_unit_id=resolved_business_unit_id),
            start_date=start_date,
            end_date=end_date,
            key_name="category_name",
            fallback=UNKNOWN_CATEGORY,
            limit=200,
        )

    def list_product_breakdown(
        self,
        *,
        scope: str,
        business_unit_id: uuid.UUID | None,
        start_date: date,
        end_date: date,
        category_name: str | None = None,
    ) -> list[DashboardProductDetailRow]:
        resolved_business_unit_id, _business_unit_name = self._resolve_business_unit(
            scope=scope,
            business_unit_id=business_unit_id,
        )
        return self._build_product_detail_breakdown(
            rows=self._list_pos_sales_rows(business_unit_id=resolved_business_unit_id),
            start_date=start_date,
            end_date=end_date,
            category_name=category_name,
            limit=200,
        )

    def list_product_source_rows(
        self,
        *,
        scope: str,
        business_unit_id: uuid.UUID | None,
        start_date: date,
        end_date: date,
        product_name: str,
        category_name: str | None = None,
        limit: int = 50,
    ) -> list[DashboardPosSourceRow]:
        resolved_business_unit_id, _business_unit_name = self._resolve_business_unit(
            scope=scope,
            business_unit_id=business_unit_id,
        )
        rows = self._list_pos_sales_rows(business_unit_id=resolved_business_unit_id)
        return self._build_product_source_rows(
            rows=rows,
            start_date=start_date,
            end_date=end_date,
            product_name=product_name,
            category_name=category_name,
            limit=limit,
        )

    def list_expense_details(
        self,
        *,
        scope: str,
        business_unit_id: uuid.UUID | None,
        start_date: date,
        end_date: date,
        transaction_type: str | None = None,
    ) -> list[DashboardExpenseDetailRow]:
        resolved_business_unit_id, _business_unit_name = self._resolve_business_unit(
            scope=scope,
            business_unit_id=business_unit_id,
        )
        transactions = self._list_financial_transactions(
            business_unit_id=resolved_business_unit_id,
            start_date=start_date,
            end_date=end_date,
        )
        expense_transactions = [
            transaction
            for transaction in transactions
            if transaction.direction == "outflow"
            and (
                transaction_type is None
                or transaction.transaction_type == transaction_type
            )
        ]
        return [
            DashboardExpenseDetailRow(
                transaction_id=transaction.id,
                transaction_type=transaction.transaction_type,
                amount=Decimal(transaction.amount),
                currency=transaction.currency,
                occurred_at=transaction.occurred_at.date(),
                description=transaction.description,
                source_type=transaction.source_type,
                source_id=transaction.source_id,
                source_layer="financial_actual",
            )
            for transaction in sorted(
                expense_transactions,
                key=lambda item: item.occurred_at,
                reverse=True,
            )[:200]
        ]

    def get_expense_source(
        self,
        *,
        transaction_id: uuid.UUID,
    ) -> DashboardExpenseSource | None:
        transaction = self._session.get(FinancialTransactionModel, transaction_id)
        if transaction is None:
            return None

        if transaction.source_type != SUPPLIER_INVOICE_SOURCE_TYPE:
            return DashboardExpenseSource(
                transaction_id=transaction.id,
                transaction_type=transaction.transaction_type,
                amount=Decimal(transaction.amount),
                currency=transaction.currency,
                occurred_at=transaction.occurred_at.date(),
                source_type=transaction.source_type,
                source_id=transaction.source_id,
                supplier_id=None,
                supplier_name=None,
                invoice_number=None,
                invoice_date=None,
                gross_total=None,
                notes=None,
                lines=(),
            )

        invoice_row = self._session.execute(
            select(PurchaseInvoiceModel, SupplierModel.name)
            .join(SupplierModel, SupplierModel.id == PurchaseInvoiceModel.supplier_id)
            .where(PurchaseInvoiceModel.id == transaction.source_id)
        ).one_or_none()
        if invoice_row is None:
            return DashboardExpenseSource(
                transaction_id=transaction.id,
                transaction_type=transaction.transaction_type,
                amount=Decimal(transaction.amount),
                currency=transaction.currency,
                occurred_at=transaction.occurred_at.date(),
                source_type=transaction.source_type,
                source_id=transaction.source_id,
                supplier_id=None,
                supplier_name=None,
                invoice_number=None,
                invoice_date=None,
                gross_total=None,
                notes=None,
                lines=(),
            )

        invoice, supplier_name = invoice_row
        lines = self._session.scalars(
            select(PurchaseInvoiceLineModel)
            .where(PurchaseInvoiceLineModel.invoice_id == invoice.id)
            .order_by(PurchaseInvoiceLineModel.description.asc())
        ).all()

        return DashboardExpenseSource(
            transaction_id=transaction.id,
            transaction_type=transaction.transaction_type,
            amount=Decimal(transaction.amount),
            currency=transaction.currency,
            occurred_at=transaction.occurred_at.date(),
            source_type=transaction.source_type,
            source_id=transaction.source_id,
            supplier_id=invoice.supplier_id,
            supplier_name=supplier_name,
            invoice_number=invoice.invoice_number,
            invoice_date=invoice.invoice_date,
            gross_total=Decimal(invoice.gross_total),
            notes=invoice.notes,
            lines=tuple(
                DashboardExpenseSourceLine(
                    line_id=line.id,
                    inventory_item_id=line.inventory_item_id,
                    description=line.description,
                    quantity=Decimal(line.quantity),
                    uom_id=line.uom_id,
                    unit_net_amount=Decimal(line.unit_net_amount),
                    line_net_amount=Decimal(line.line_net_amount),
                )
                for line in lines
            ),
        )

    def list_basket_pairs(
        self,
        *,
        scope: str,
        business_unit_id: uuid.UUID | None,
        start_date: date,
        end_date: date,
        limit: int = 20,
    ) -> list[DashboardBasketPairRow]:
        resolved_business_unit_id, _business_unit_name = self._resolve_business_unit(
            scope=scope,
            business_unit_id=business_unit_id,
        )
        return self._build_basket_pairs(
            rows=self._list_pos_sales_rows(business_unit_id=resolved_business_unit_id),
            start_date=start_date,
            end_date=end_date,
            limit=limit,
        )

    def list_basket_pair_receipts(
        self,
        *,
        scope: str,
        business_unit_id: uuid.UUID | None,
        start_date: date,
        end_date: date,
        product_a: str,
        product_b: str,
        limit: int = 20,
    ) -> list[DashboardBasketReceipt]:
        resolved_business_unit_id, _business_unit_name = self._resolve_business_unit(
            scope=scope,
            business_unit_id=business_unit_id,
        )
        return self._build_basket_pair_receipts(
            rows=self._list_pos_sales_rows(business_unit_id=resolved_business_unit_id),
            start_date=start_date,
            end_date=end_date,
            product_a=product_a,
            product_b=product_b,
            limit=limit,
        )

    def _resolve_business_unit(
        self,
        *,
        scope: str,
        business_unit_id: uuid.UUID | None,
    ) -> tuple[uuid.UUID | None, str | None]:
        if business_unit_id is not None:
            model = self._session.get(BusinessUnitModel, business_unit_id)
            return business_unit_id, model.name if model else None

        business_unit_code = BUSINESS_SCOPE_CODES.get(scope)
        if business_unit_code is None:
            return None, None

        model = self._session.scalar(
            select(BusinessUnitModel).where(BusinessUnitModel.code == business_unit_code)
        )
        if model is None:
            return None, None

        return model.id, model.name

    def _list_financial_transactions(
        self,
        *,
        business_unit_id: uuid.UUID | None,
        start_date: date,
        end_date: date,
    ) -> list[FinancialTransactionModel]:
        start_at = datetime.combine(start_date, time.min, tzinfo=APP_TIME_ZONE)
        end_at = datetime.combine(end_date, time.max, tzinfo=APP_TIME_ZONE)
        statement = select(FinancialTransactionModel).where(
            FinancialTransactionModel.occurred_at >= start_at,
            FinancialTransactionModel.occurred_at <= end_at,
        )

        if business_unit_id is not None:
            statement = statement.where(
                FinancialTransactionModel.business_unit_id == business_unit_id
            )

        return list(self._session.scalars(statement).all())

    def _list_pos_sales_rows(
        self,
        *,
        business_unit_id: uuid.UUID | None,
    ) -> list[ImportRowModel]:
        statement = (
            select(ImportRowModel)
            .join(ImportBatchModel, ImportBatchModel.id == ImportRowModel.batch_id)
            .where(ImportBatchModel.import_type == "pos_sales")
            .where(ImportRowModel.parse_status == "parsed")
        )

        if business_unit_id is not None:
            statement = statement.where(ImportBatchModel.business_unit_id == business_unit_id)

        return list(self._session.scalars(statement).all())

    @staticmethod
    def _sum_transactions(
        transactions: list[FinancialTransactionModel],
        *,
        direction: str,
    ) -> Decimal:
        return sum(
            (
                Decimal(transaction.amount)
                for transaction in transactions
                if transaction.direction == direction
            ),
            Decimal("0"),
        )

    def _build_product_unit_costs(
        self,
        *,
        business_unit_id: uuid.UUID | None,
    ) -> dict[str, Decimal]:
        product_statement = (
            select(ProductModel, UnitOfMeasureModel.code)
            .outerjoin(UnitOfMeasureModel, ProductModel.sales_uom_id == UnitOfMeasureModel.id)
            .where(ProductModel.is_active.is_(True))
        )
        if business_unit_id is not None:
            product_statement = product_statement.where(
                ProductModel.business_unit_id == business_unit_id
            )

        latest_item_costs = self._build_latest_inventory_item_costs()
        recipe_costs = self._build_recipe_product_unit_costs(latest_item_costs)
        costs: dict[str, Decimal] = {}

        for product, sales_uom_code in self._session.execute(product_statement).all():
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

    def _build_latest_inventory_item_costs(self) -> dict[uuid.UUID, Decimal]:
        costs = {
            item.id: Decimal(item.default_unit_cost)
            for item in self._session.scalars(select(InventoryItemModel)).all()
            if item.default_unit_cost is not None
        }

        invoice_rows = self._session.execute(
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
        for line, _invoice_date in invoice_rows:
            if line.inventory_item_id is not None:
                costs[line.inventory_item_id] = Decimal(line.unit_net_amount)

        return costs

    def _build_recipe_product_unit_costs(
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

        product_costs: dict[uuid.UUID, Decimal] = {}
        for product_id, version_id, yield_quantity in versions:
            ingredients = self._session.execute(
                select(RecipeIngredientModel, InventoryItemModel.uom_id)
                .join(
                    InventoryItemModel,
                    InventoryItemModel.id == RecipeIngredientModel.inventory_item_id,
                )
                .where(RecipeIngredientModel.recipe_version_id == version_id)
            ).all()
            total_cost = Decimal("0")
            for ingredient, item_uom_id in ingredients:
                unit_cost = item_costs.get(ingredient.inventory_item_id)
                if unit_cost is None:
                    continue
                quantity = self._convert_quantity(
                    Decimal(ingredient.quantity),
                    from_uom=uom_codes.get(ingredient.uom_id),
                    to_uom=uom_codes.get(item_uom_id),
                )
                total_cost += quantity * unit_cost

            yield_qty = Decimal(yield_quantity)
            if yield_qty > 0:
                product_costs[product_id] = total_cost / yield_qty

        return product_costs

    def _sum_estimated_cogs(
        self,
        *,
        rows: list[ImportRowModel],
        product_costs: dict[str, Decimal],
        start_date: date,
        end_date: date,
    ) -> Decimal:
        total = Decimal("0")
        for row in rows:
            payload = row.normalized_payload or {}
            row_date = self._parse_payload_date(payload.get("date"))
            if row_date is None or row_date < start_date or row_date > end_date:
                continue
            total += (
                self._lookup_payload_unit_cost(payload, product_costs)
                * self._parse_decimal(payload.get("quantity"))
            )
        return total

    def _build_trend(
        self,
        *,
        transactions: list[FinancialTransactionModel],
        rows: list[ImportRowModel],
        product_costs: dict[str, Decimal],
        start_date: date,
        end_date: date,
        grain: str,
    ) -> list[DashboardTrendPoint]:
        buckets = {
            bucket: {
                "revenue": Decimal("0"),
                "cost": Decimal("0"),
                "estimated_cogs": Decimal("0"),
            }
            for bucket in self._iter_buckets(start_date=start_date, end_date=end_date, grain=grain)
        }

        for transaction in transactions:
            bucket = self._bucket_date(
                self._local_business_date(transaction.occurred_at),
                grain=grain,
            )
            if bucket not in buckets:
                continue

            if transaction.direction == "inflow":
                buckets[bucket]["revenue"] += Decimal(transaction.amount)
            elif transaction.direction == "outflow":
                buckets[bucket]["cost"] += Decimal(transaction.amount)

        for row in rows:
            payload = row.normalized_payload or {}
            row_date = self._parse_payload_date(payload.get("date"))
            if row_date is None or row_date < start_date or row_date > end_date:
                continue
            bucket = self._bucket_date(row_date, grain=grain)
            if bucket not in buckets:
                continue
            buckets[bucket]["estimated_cogs"] += (
                self._lookup_payload_unit_cost(payload, product_costs)
                * self._parse_decimal(payload.get("quantity"))
            )

        return [
            DashboardTrendPoint(
                period_start=bucket,
                revenue=values["revenue"],
                cost=values["cost"],
                profit=values["revenue"] - values["cost"],
                estimated_cogs=values["estimated_cogs"],
                margin_profit=values["revenue"] - values["estimated_cogs"],
            )
            for bucket, values in buckets.items()
        ]

    def _build_pos_breakdown(
        self,
        *,
        rows: list[ImportRowModel],
        start_date: date,
        end_date: date,
        key_name: str,
        fallback: str,
        limit: int,
    ) -> list[DashboardBreakdownRow]:
        aggregate: dict[str, dict[str, Decimal | int]] = defaultdict(
            lambda: {"revenue": Decimal("0"), "quantity": Decimal("0"), "count": 0}
        )

        for row in rows:
            payload = row.normalized_payload or {}
            row_date = self._parse_payload_date(payload.get("date"))
            if row_date is None or row_date < start_date or row_date > end_date:
                continue

            label = self._extract_text(payload.get(key_name), fallback=fallback)
            aggregate[label]["revenue"] += self._parse_decimal(payload.get("gross_amount"))
            aggregate[label]["quantity"] += self._parse_decimal(payload.get("quantity"))
            aggregate[label]["count"] += 1

        sorted_rows = sorted(
            aggregate.items(),
            key=lambda item: Decimal(item[1]["revenue"]),
            reverse=True,
        )
        return [
            DashboardBreakdownRow(
                label=label,
                revenue=Decimal(values["revenue"]),
                quantity=Decimal(values["quantity"]),
                transaction_count=int(values["count"]),
                source_layer="import_derived",
            )
            for label, values in sorted_rows[:limit]
        ]

    def _build_product_detail_breakdown(
        self,
        *,
        rows: list[ImportRowModel],
        start_date: date,
        end_date: date,
        category_name: str | None,
        limit: int,
    ) -> list[DashboardProductDetailRow]:
        aggregate: dict[tuple[str, str], dict[str, Decimal | int]] = defaultdict(
            lambda: {"revenue": Decimal("0"), "quantity": Decimal("0"), "count": 0}
        )

        for row in rows:
            payload = row.normalized_payload or {}
            row_date = self._parse_payload_date(payload.get("date"))
            if row_date is None or row_date < start_date or row_date > end_date:
                continue

            category = self._extract_text(
                payload.get("category_name"),
                fallback=UNKNOWN_CATEGORY,
            )
            if category_name is not None and category != category_name:
                continue

            product = self._extract_text(
                payload.get("product_name"),
                fallback=UNKNOWN_PRODUCT,
            )
            key = (product, category)
            aggregate[key]["revenue"] += self._parse_decimal(payload.get("gross_amount"))
            aggregate[key]["quantity"] += self._parse_decimal(payload.get("quantity"))
            aggregate[key]["count"] += 1

        sorted_rows = sorted(
            aggregate.items(),
            key=lambda item: Decimal(item[1]["revenue"]),
            reverse=True,
        )
        return [
            DashboardProductDetailRow(
                product_name=product,
                category_name=category,
                revenue=Decimal(values["revenue"]),
                quantity=Decimal(values["quantity"]),
                transaction_count=int(values["count"]),
                source_layer="import_derived",
            )
            for (product, category), values in sorted_rows[:limit]
        ]

    def _build_product_source_rows(
        self,
        *,
        rows: list[ImportRowModel],
        start_date: date,
        end_date: date,
        product_name: str,
        category_name: str | None,
        limit: int,
    ) -> list[DashboardPosSourceRow]:
        source_rows: list[DashboardPosSourceRow] = []
        for row in rows:
            payload = row.normalized_payload or {}
            row_date = self._parse_payload_date(payload.get("date"))
            if row_date is None or row_date < start_date or row_date > end_date:
                continue

            category = self._extract_text(
                payload.get("category_name"),
                fallback=UNKNOWN_CATEGORY,
            )
            product = self._extract_text(
                payload.get("product_name"),
                fallback=UNKNOWN_PRODUCT,
            )
            if product != product_name:
                continue
            if category_name is not None and category != category_name:
                continue

            source_rows.append(
                DashboardPosSourceRow(
                    row_id=row.id,
                    row_number=row.row_number,
                    date=row_date,
                    receipt_no=self._extract_optional_text(payload.get("receipt_no")),
                    category_name=category,
                    product_name=product,
                    quantity=self._parse_decimal(payload.get("quantity")),
                    gross_amount=self._parse_decimal(payload.get("gross_amount")),
                    payment_method=self._extract_optional_text(
                        payload.get("payment_method")
                    ),
                    source_layer="import_derived",
                )
            )

        return sorted(
            source_rows,
            key=lambda item: (item.date or date.min, item.row_number),
            reverse=True,
        )[:limit]

    def _build_basket_metrics(
        self,
        *,
        rows: list[ImportRowModel],
        start_date: date,
        end_date: date,
    ) -> tuple[Decimal, Decimal]:
        baskets: dict[str, dict[str, Decimal]] = defaultdict(
            lambda: {"gross_amount": Decimal("0"), "quantity": Decimal("0")}
        )

        for row in rows:
            payload = row.normalized_payload or {}
            row_date = self._parse_payload_date(payload.get("date"))
            if row_date is None or row_date < start_date or row_date > end_date:
                continue

            receipt_no = self._extract_optional_text(payload.get("receipt_no"))
            basket_key = receipt_no or str(row.id)
            baskets[basket_key]["gross_amount"] += self._parse_decimal(
                payload.get("gross_amount")
            )
            baskets[basket_key]["quantity"] += self._parse_decimal(
                payload.get("quantity")
            )

        basket_count = len(baskets)
        if basket_count == 0:
            return Decimal("0"), Decimal("0")

        total_amount = sum(
            (values["gross_amount"] for values in baskets.values()),
            Decimal("0"),
        )
        total_quantity = sum(
            (values["quantity"] for values in baskets.values()),
            Decimal("0"),
        )
        return total_amount / basket_count, total_quantity / basket_count

    def _build_basket_pairs(
        self,
        *,
        rows: list[ImportRowModel],
        start_date: date,
        end_date: date,
        limit: int,
    ) -> list[DashboardBasketPairRow]:
        baskets: dict[str, dict[str, Decimal]] = defaultdict(lambda: defaultdict(Decimal))

        for row in rows:
            payload = row.normalized_payload or {}
            row_date = self._parse_payload_date(payload.get("date"))
            if row_date is None or row_date < start_date or row_date > end_date:
                continue

            product = self._extract_text(
                payload.get("product_name"),
                fallback=UNKNOWN_PRODUCT,
            )
            if product == UNKNOWN_PRODUCT:
                continue

            receipt_no = self._extract_optional_text(payload.get("receipt_no"))
            basket_key = receipt_no or str(row.id)
            baskets[basket_key][product] += self._parse_decimal(
                payload.get("gross_amount")
            )

        pair_aggregate: dict[tuple[str, str], dict[str, Decimal | int]] = defaultdict(
            lambda: {"basket_count": 0, "total_gross_amount": Decimal("0")}
        )
        for products in baskets.values():
            unique_products = sorted(products.keys())
            if len(unique_products) < 2:
                continue

            for product_a, product_b in combinations(unique_products, 2):
                pair = (product_a, product_b)
                pair_aggregate[pair]["basket_count"] += 1
                pair_aggregate[pair]["total_gross_amount"] += (
                    products[product_a] + products[product_b]
                )

        sorted_pairs = sorted(
            pair_aggregate.items(),
            key=lambda item: (
                int(item[1]["basket_count"]),
                Decimal(item[1]["total_gross_amount"]),
                item[0][0],
                item[0][1],
            ),
            reverse=True,
        )
        return [
            DashboardBasketPairRow(
                product_a=product_a,
                product_b=product_b,
                basket_count=int(values["basket_count"]),
                total_gross_amount=Decimal(values["total_gross_amount"]),
                source_layer="import_derived",
            )
            for (product_a, product_b), values in sorted_pairs[:limit]
        ]

    def _build_basket_pair_receipts(
        self,
        *,
        rows: list[ImportRowModel],
        start_date: date,
        end_date: date,
        product_a: str,
        product_b: str,
        limit: int,
    ) -> list[DashboardBasketReceipt]:
        basket_rows: dict[str, list[ImportRowModel]] = defaultdict(list)

        for row in rows:
            payload = row.normalized_payload or {}
            row_date = self._parse_payload_date(payload.get("date"))
            if row_date is None or row_date < start_date or row_date > end_date:
                continue

            receipt_no = self._extract_optional_text(payload.get("receipt_no"))
            if receipt_no is None:
                continue
            basket_rows[receipt_no].append(row)

        receipts: list[DashboardBasketReceipt] = []
        for receipt_no, receipt_rows in basket_rows.items():
            products = {
                self._extract_text(
                    (row.normalized_payload or {}).get("product_name"),
                    fallback=UNKNOWN_PRODUCT,
                )
                for row in receipt_rows
            }
            if product_a not in products or product_b not in products:
                continue

            receipt_date = None
            total_gross_amount = Decimal("0")
            total_quantity = Decimal("0")
            lines: list[DashboardBasketReceiptLine] = []
            for row in sorted(receipt_rows, key=lambda item: item.row_number):
                payload = row.normalized_payload or {}
                row_date = self._parse_payload_date(payload.get("date"))
                receipt_date = receipt_date or row_date
                quantity = self._parse_decimal(payload.get("quantity"))
                gross_amount = self._parse_decimal(payload.get("gross_amount"))
                total_quantity += quantity
                total_gross_amount += gross_amount
                lines.append(
                    DashboardBasketReceiptLine(
                        row_id=row.id,
                        row_number=row.row_number,
                        product_name=self._extract_text(
                            payload.get("product_name"),
                            fallback=UNKNOWN_PRODUCT,
                        ),
                        category_name=self._extract_text(
                            payload.get("category_name"),
                            fallback=UNKNOWN_CATEGORY,
                        ),
                        quantity=quantity,
                        gross_amount=gross_amount,
                        payment_method=self._extract_optional_text(
                            payload.get("payment_method")
                        ),
                    )
                )

            receipts.append(
                DashboardBasketReceipt(
                    receipt_no=receipt_no,
                    date=receipt_date,
                    gross_amount=total_gross_amount,
                    quantity=total_quantity,
                    lines=tuple(lines),
                    source_layer="import_derived",
                )
            )

        return sorted(
            receipts,
            key=lambda item: (item.date or date.min, item.gross_amount, item.receipt_no),
            reverse=True,
        )[:limit]

    @staticmethod
    def _build_expense_breakdown(
        *,
        transactions: list[FinancialTransactionModel],
        limit: int,
    ) -> list[DashboardExpenseRow]:
        aggregate: dict[str, dict[str, Decimal | int]] = defaultdict(
            lambda: {"amount": Decimal("0"), "count": 0}
        )

        for transaction in transactions:
            if transaction.direction != "outflow":
                continue

            label = transaction.transaction_type or "expense"
            aggregate[label]["amount"] += Decimal(transaction.amount)
            aggregate[label]["count"] += 1

        sorted_rows = sorted(
            aggregate.items(),
            key=lambda item: Decimal(item[1]["amount"]),
            reverse=True,
        )
        return [
            DashboardExpenseRow(
                label=label,
                amount=Decimal(values["amount"]),
                transaction_count=int(values["count"]),
                source_layer="financial_actual",
            )
            for label, values in sorted_rows[:limit]
        ]

    @staticmethod
    def _iter_buckets(
        *,
        start_date: date,
        end_date: date,
        grain: str,
    ) -> list[date]:
        buckets: list[date] = []
        current = start_date.replace(day=1) if grain == "month" else start_date
        while current <= end_date:
            buckets.append(current)
            if grain == "month":
                current = (
                    current.replace(year=current.year + 1, month=1)
                    if current.month == 12
                    else current.replace(month=current.month + 1)
                )
            else:
                current = current.fromordinal(current.toordinal() + 1)
        return buckets

    @staticmethod
    def _bucket_date(value: date, *, grain: str) -> date:
        if grain == "month":
            return value.replace(day=1)
        return value

    @staticmethod
    def _parse_payload_date(value: Any) -> date | None:
        if not isinstance(value, str):
            return None
        try:
            return date.fromisoformat(value)
        except ValueError:
            return None

    @staticmethod
    def _local_business_date(value: datetime) -> date:
        if value.tzinfo is None:
            return value.date()
        return value.astimezone(APP_TIME_ZONE).date()

    @staticmethod
    def _parse_decimal(value: Any) -> Decimal:
        if value is None:
            return Decimal("0")
        try:
            return Decimal(str(value))
        except (InvalidOperation, ValueError):
            return Decimal("0")

    @classmethod
    def _lookup_payload_unit_cost(
        cls,
        payload: dict[str, Any],
        product_costs: dict[str, Decimal],
    ) -> Decimal:
        for key_name in ("product_id", "sku", "product_name"):
            value = payload.get(key_name)
            if isinstance(value, str) and value in product_costs:
                return product_costs[value]
        return Decimal("0")

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
        from_factor = factors.get(from_uom)
        to_factor = factors.get(to_uom)
        if from_factor is None or to_factor is None or from_factor[0] != to_factor[0]:
            return quantity

        return (quantity * from_factor[1]) / to_factor[1]

    @staticmethod
    def _extract_text(value: Any, *, fallback: str) -> str:
        if isinstance(value, str) and value.strip():
            return value.strip()
        return fallback

    @staticmethod
    def _extract_optional_text(value: Any) -> str | None:
        if isinstance(value, str) and value.strip():
            return value.strip()
        return None
