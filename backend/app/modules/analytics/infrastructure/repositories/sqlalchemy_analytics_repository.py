"""SQLAlchemy analytics read-model repository."""

from __future__ import annotations

import uuid
from collections import defaultdict
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from typing import Any
from zoneinfo import ZoneInfo

import sqlalchemy as sa
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.analytics.domain.entities.dashboard_snapshot import (
    DashboardBasketPairRow,
    DashboardBasketReceipt,
    DashboardBreakdownRow,
    DashboardCategoryTrendRow,
    DashboardExpenseDetailRow,
    DashboardExpenseSource,
    DashboardHeatmapCell,
    DashboardKpi,
    DashboardPeriod,
    DashboardProductRiskRow,
    DashboardPosSourceRow,
    DashboardProductDetailRow,
    DashboardSnapshot,
    DashboardStockRiskRow,
    DashboardVatReadiness,
)
from app.modules.analytics.infrastructure.repositories.expense_analytics_reader import (
    ExpenseAnalyticsReader,
)
from app.modules.analytics.infrastructure.repositories.forecast_analytics_reader import (
    ForecastAnalyticsReader,
)
from app.modules.analytics.infrastructure.repositories.forecast_demand_analytics_builder import (
    ForecastDemandAnalyticsBuilder,
)
from app.modules.analytics.infrastructure.repositories.forecast_operations_analytics_reader import (
    ForecastOperationsAnalyticsReader,
)
from app.modules.analytics.infrastructure.repositories.pos_financial_metrics import (
    lookup_payload_vat_rate,
    tax_breakdown_source,
)
from app.modules.analytics.infrastructure.repositories.pos_sales_analytics_builder import (
    PosSalesAnalyticsBuilder,
)
from app.modules.analytics.infrastructure.repositories.weather_analytics_reader import (
    WeatherAnalyticsReader,
)
from app.modules.finance.infrastructure.orm.transaction_model import (
    FinancialTransactionModel,
)
from app.modules.imports.infrastructure.orm.import_batch_model import ImportBatchModel
from app.modules.imports.infrastructure.orm.import_row_model import ImportRowModel
from app.modules.inventory.infrastructure.orm.inventory_item_model import (
    InventoryItemModel,
)
from app.modules.inventory.infrastructure.orm.inventory_movement_model import (
    InventoryMovementModel,
)
from app.modules.master_data.infrastructure.orm.business_unit_model import (
    BusinessUnitModel,
)
from app.modules.master_data.infrastructure.orm.category_model import CategoryModel
from app.modules.master_data.infrastructure.orm.product_model import ProductModel
from app.modules.master_data.infrastructure.orm.vat_rate_model import VatRateModel
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
from app.modules.weather.application.commands.sync_shared_weather import (
    SHARED_WEATHER_LOCATION_NAME,
    SHARED_WEATHER_PROVIDER,
)

BUSINESS_SCOPE_CODES = {
    "flow": "flow",
    "gourmand": "gourmand",
}
UNKNOWN_CATEGORY = "Kategória nélkül"
UNKNOWN_PRODUCT = "Ismeretlen termék"
APP_TIME_ZONE = ZoneInfo("Europe/Budapest")
FORECAST_IMPACT_DAYS = 7


class SqlAlchemyAnalyticsRepository:
    """Build dashboard read models from operational actuals and import rows."""

    def __init__(self, session: Session) -> None:
        self._session = session
        self._pos_sales = PosSalesAnalyticsBuilder(
            time_zone=APP_TIME_ZONE,
            unknown_category=UNKNOWN_CATEGORY,
            unknown_product=UNKNOWN_PRODUCT,
        )
        self._expenses = ExpenseAnalyticsReader(session)
        self._weather = WeatherAnalyticsReader(
            session,
            time_zone=APP_TIME_ZONE,
            location_name=SHARED_WEATHER_LOCATION_NAME,
            provider=SHARED_WEATHER_PROVIDER,
            unknown_category=UNKNOWN_CATEGORY,
        )
        self._forecast = ForecastAnalyticsReader(
            session,
            time_zone=APP_TIME_ZONE,
            location_name=SHARED_WEATHER_LOCATION_NAME,
            provider=SHARED_WEATHER_PROVIDER,
        )
        self._forecast_demand = ForecastDemandAnalyticsBuilder(
            forecast_reader=self._forecast,
            weather_reader=self._weather,
            time_zone=APP_TIME_ZONE,
            unknown_category=UNKNOWN_CATEGORY,
            unknown_product=UNKNOWN_PRODUCT,
            horizon_days=FORECAST_IMPACT_DAYS,
        )
        self._forecast_operations = ForecastOperationsAnalyticsReader(
            session,
            forecast_reader=self._forecast,
            time_zone=APP_TIME_ZONE,
            horizon_days=FORECAST_IMPACT_DAYS,
        )

    def get_business_dashboard(
        self,
        *,
        scope: str,
        business_unit_id: uuid.UUID | None,
        preset: str,
        start_at: datetime,
        end_at: datetime,
        grain: str,
    ) -> DashboardSnapshot:
        resolved_business_unit_id, business_unit_name = self._resolve_business_unit(
            scope=scope,
            business_unit_id=business_unit_id,
        )
        transactions = self._list_financial_transactions(
            business_unit_id=resolved_business_unit_id,
            start_at=start_at,
            end_at=end_at,
        )
        import_rows = self._list_pos_sales_rows(
            business_unit_id=resolved_business_unit_id,
        )
        product_costs = self._build_product_unit_costs(
            business_unit_id=resolved_business_unit_id,
        )
        product_vat_rates = self._build_product_vat_rates(
            business_unit_id=resolved_business_unit_id,
        )

        revenue = self._sum_transactions(transactions, direction="inflow")
        cost = self._sum_transactions(transactions, direction="outflow")
        profit = revenue - cost
        estimated_cogs = self._pos_sales.sum_estimated_cogs(
            rows=import_rows,
            product_costs=product_costs,
            start_at=start_at,
            end_at=end_at,
        )
        margin_profit = revenue - estimated_cogs
        transaction_count = len(transactions)
        profit_margin = (
            (margin_profit / revenue * Decimal("100"))
            if revenue > Decimal("0")
            else Decimal("0")
        )
        average_basket_value, average_basket_quantity = (
            self._pos_sales.build_basket_metrics(
            rows=import_rows,
            start_at=start_at,
            end_at=end_at,
            )
        )
        forecast_category_demand_insights = tuple(
            self._forecast_demand.build_category_demand(
                rows=import_rows,
                scope=scope,
            )
        )

        return DashboardSnapshot(
            scope=scope,
            business_unit_id=resolved_business_unit_id,
            business_unit_name=business_unit_name,
            period=DashboardPeriod(
                preset=preset,
                start_date=start_at.date(),
                end_date=end_at.date(),
                grain=grain,
            ),
            kpis=(
                DashboardKpi(
                    "revenue",
                    "Bevétel",
                    revenue,
                    "HUF",
                    "financial_actual",
                    "gross",
                    "actual",
                ),
                DashboardKpi(
                    "cost",
                    "Kiadás",
                    cost,
                    "HUF",
                    "financial_actual",
                    "gross",
                    "actual",
                ),
                DashboardKpi(
                    "profit",
                    "Profit",
                    profit,
                    "HUF",
                    "derived_actual",
                    "gross",
                    "derived",
                ),
                DashboardKpi(
                    "estimated_cogs",
                    "Becsült eladott áruk költsége",
                    estimated_cogs,
                    "HUF",
                    "recipe_or_unit_cost",
                    "net",
                    "derived",
                ),
                DashboardKpi(
                    "transaction_count",
                    "Tranzakciók",
                    Decimal(transaction_count),
                    "count",
                    "financial_actual",
                ),
                DashboardKpi(
                    "profit_margin",
                    "Árrés profit",
                    margin_profit,
                    "HUF",
                    "recipe_or_unit_cost",
                    "mixed",
                    "derived",
                ),
                DashboardKpi(
                    "gross_margin_percent",
                    "Árrés %",
                    profit_margin,
                    "%",
                    "recipe_or_unit_cost",
                    "mixed",
                    "derived",
                ),
                DashboardKpi(
                    "average_basket_value",
                    "Átlagkosár érték",
                    average_basket_value,
                    "HUF",
                    "import_derived",
                    "gross",
                    "actual",
                ),
                DashboardKpi(
                    "average_basket_quantity",
                    "Átlagkosár mennyiség",
                    average_basket_quantity,
                    "count",
                    "import_derived",
                ),
            ),
            revenue_trend=tuple(
                self._pos_sales.build_trend(
                    transactions=transactions,
                    rows=import_rows,
                    product_costs=product_costs,
                    start_at=start_at,
                    end_at=end_at,
                    grain=grain,
                )
            ),
            category_breakdown=tuple(
                self._pos_sales.build_breakdown(
                    rows=import_rows,
                    start_at=start_at,
                    end_at=end_at,
                    key_name="category_name",
                    fallback=UNKNOWN_CATEGORY,
                    limit=12,
                    product_vat_rates=product_vat_rates,
                )
            ),
            vat_readiness=self._build_vat_readiness(
                rows=import_rows,
                start_at=start_at,
                end_at=end_at,
                product_vat_rates=product_vat_rates,
            ),
            payment_method_breakdown=tuple(
                self._pos_sales.build_breakdown(
                    rows=import_rows,
                    start_at=start_at,
                    end_at=end_at,
                    key_name="payment_method",
                    fallback="unknown",
                    limit=8,
                    product_vat_rates=product_vat_rates,
                )
            ),
            basket_value_distribution=tuple(
                self._pos_sales.build_basket_value_distribution(
                    rows=import_rows,
                    start_at=start_at,
                    end_at=end_at,
                )
            ),
            traffic_heatmap=tuple(
                self._build_traffic_heatmap(
                    rows=import_rows,
                    start_at=start_at,
                    end_at=end_at,
                )
            ),
            category_trends=tuple(
                self._build_category_trends(
                    rows=import_rows,
                    start_at=start_at,
                    end_at=end_at,
                    limit=8,
                )
            ),
            weather_category_insights=tuple(
                self._weather.build_category_insights(
                    rows=import_rows,
                    start_at=start_at,
                    end_at=end_at,
                    limit=8,
                )
            ),
            temperature_band_insights=tuple(
                self._weather.build_temperature_band_insights(
                    rows=import_rows,
                    start_at=start_at,
                    end_at=end_at,
                )
            ),
            weather_condition_insights=tuple(
                self._weather.build_condition_insights(
                    rows=import_rows,
                    start_at=start_at,
                    end_at=end_at,
                )
            ),
            forecast_impact_insights=tuple(
                self._forecast_demand.build_impact(
                    rows=import_rows,
                    scope=scope,
                )
            ),
            forecast_category_demand_insights=forecast_category_demand_insights,
            forecast_preparation_insights=tuple(
                self._forecast_operations.build_preparation(
                    business_unit_id=resolved_business_unit_id,
                    scope=scope,
                    demand_rows=list(forecast_category_demand_insights),
                    recipe_ingredients=self._build_active_recipe_ingredients(
                        business_unit_id=resolved_business_unit_id,
                    ),
                    stock_levels=self._build_inventory_stock_level_summary(
                        business_unit_id=resolved_business_unit_id,
                    ),
                    limit=10,
                )
            ),
            forecast_product_demand_insights=tuple(
                self._forecast_demand.build_product_demand(
                    rows=import_rows,
                    scope=scope,
                )
            ),
            forecast_peak_time_insights=tuple(
                self._forecast_demand.build_peak_times(
                    rows=import_rows,
                    scope=scope,
                )
            ),
            flow_forecast_event_insights=tuple(
                self._forecast_operations.build_flow_events(
                    business_unit_id=resolved_business_unit_id,
                    scope=scope,
                    limit=8,
                )
            ),
            product_risks=tuple(
                self._build_product_risks(
                    business_unit_id=resolved_business_unit_id,
                    limit=8,
                )
            ),
            stock_risks=tuple(
                self._build_stock_risks(
                    business_unit_id=resolved_business_unit_id,
                    limit=8,
                )
            ),
            top_products=tuple(
                self._pos_sales.build_breakdown(
                    rows=import_rows,
                    start_at=start_at,
                    end_at=end_at,
                    key_name="product_name",
                    fallback=UNKNOWN_PRODUCT,
                    limit=10,
                    product_vat_rates=product_vat_rates,
                )
            ),
            expense_breakdown=tuple(
                self._expenses.build_breakdown(transactions=transactions, limit=10)
            ),
            notes=(
                "A pénzügyi KPI-k a rögzített pénzügyi tranzakciókból számolódnak.",
                "A kiadás az adott időszakban rögzített tényleges kimenő pénzmozgás.",
                "A termék- és kategóriabontás az adatbázisba mentett kasszasorokból készül.",
                "Az átlagkosár mutatók a nyugtaszám szerinti kasszacsoportokból számolódnak.",
                "A profit bevétel mínusz rögzített kiadás, az árrés pedig becsült recept- vagy egységköltség alapján készül.",
            ),
        )

    def list_category_breakdown(
        self,
        *,
        scope: str,
        business_unit_id: uuid.UUID | None,
        start_at: datetime,
        end_at: datetime,
    ) -> list[DashboardBreakdownRow]:
        resolved_business_unit_id, _business_unit_name = self._resolve_business_unit(
            scope=scope,
            business_unit_id=business_unit_id,
        )
        return self._pos_sales.build_breakdown(
            rows=self._list_pos_sales_rows(business_unit_id=resolved_business_unit_id),
            start_at=start_at,
            end_at=end_at,
            key_name="category_name",
            fallback=UNKNOWN_CATEGORY,
            limit=200,
            product_vat_rates=self._build_product_vat_rates(
                business_unit_id=resolved_business_unit_id,
            ),
        )

    def list_product_breakdown(
        self,
        *,
        scope: str,
        business_unit_id: uuid.UUID | None,
        start_at: datetime,
        end_at: datetime,
        category_name: str | None = None,
    ) -> list[DashboardProductDetailRow]:
        resolved_business_unit_id, _business_unit_name = self._resolve_business_unit(
            scope=scope,
            business_unit_id=business_unit_id,
        )
        return self._pos_sales.build_product_details(
            rows=self._list_pos_sales_rows(business_unit_id=resolved_business_unit_id),
            start_at=start_at,
            end_at=end_at,
            category_name=category_name,
            limit=200,
            product_costs=self._build_product_unit_costs(
                business_unit_id=resolved_business_unit_id,
            ),
            product_vat_rates=self._build_product_vat_rates(
                business_unit_id=resolved_business_unit_id,
            ),
        )

    def list_product_source_rows(
        self,
        *,
        scope: str,
        business_unit_id: uuid.UUID | None,
        start_at: datetime,
        end_at: datetime,
        product_name: str,
        category_name: str | None = None,
        limit: int = 50,
    ) -> list[DashboardPosSourceRow]:
        resolved_business_unit_id, _business_unit_name = self._resolve_business_unit(
            scope=scope,
            business_unit_id=business_unit_id,
        )
        rows = self._list_pos_sales_rows(business_unit_id=resolved_business_unit_id)
        return self._pos_sales.build_product_source_rows(
            rows=rows,
            start_at=start_at,
            end_at=end_at,
            product_name=product_name,
            category_name=category_name,
            limit=limit,
            product_vat_rates=self._build_product_vat_rates(
                business_unit_id=resolved_business_unit_id,
            ),
        )

    def list_expense_details(
        self,
        *,
        scope: str,
        business_unit_id: uuid.UUID | None,
        start_at: datetime,
        end_at: datetime,
        transaction_type: str | None = None,
    ) -> list[DashboardExpenseDetailRow]:
        resolved_business_unit_id, _business_unit_name = self._resolve_business_unit(
            scope=scope,
            business_unit_id=business_unit_id,
        )
        transactions = self._list_financial_transactions(
            business_unit_id=resolved_business_unit_id,
            start_at=start_at,
            end_at=end_at,
        )
        return self._expenses.list_details(
            transactions=transactions,
            transaction_type=transaction_type,
        )

    def get_expense_source(
        self,
        *,
        transaction_id: uuid.UUID,
    ) -> DashboardExpenseSource | None:
        return self._expenses.get_source(transaction_id=transaction_id)

    def list_basket_pairs(
        self,
        *,
        scope: str,
        business_unit_id: uuid.UUID | None,
        start_at: datetime,
        end_at: datetime,
        limit: int = 20,
    ) -> list[DashboardBasketPairRow]:
        resolved_business_unit_id, _business_unit_name = self._resolve_business_unit(
            scope=scope,
            business_unit_id=business_unit_id,
        )
        return self._pos_sales.build_basket_pairs(
            rows=self._list_pos_sales_rows(business_unit_id=resolved_business_unit_id),
            start_at=start_at,
            end_at=end_at,
            limit=limit,
        )

    def list_basket_pair_receipts(
        self,
        *,
        scope: str,
        business_unit_id: uuid.UUID | None,
        start_at: datetime,
        end_at: datetime,
        product_a: str,
        product_b: str,
        limit: int = 20,
    ) -> list[DashboardBasketReceipt]:
        resolved_business_unit_id, _business_unit_name = self._resolve_business_unit(
            scope=scope,
            business_unit_id=business_unit_id,
        )
        return self._pos_sales.build_basket_pair_receipts(
            rows=self._list_pos_sales_rows(business_unit_id=resolved_business_unit_id),
            start_at=start_at,
            end_at=end_at,
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
        start_at: datetime,
        end_at: datetime,
    ) -> list[FinancialTransactionModel]:
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
            .where(
                ImportBatchModel.import_type.in_(
                    ("pos_sales", "gourmand_pos_sales", "flow_pos_sales")
                )
            )
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

    def _build_product_vat_rates(
        self,
        *,
        business_unit_id: uuid.UUID | None,
    ) -> dict[str, Decimal]:
        statement = (
            select(ProductModel, VatRateModel.rate_percent)
            .join(VatRateModel, ProductModel.default_vat_rate_id == VatRateModel.id)
            .where(ProductModel.is_active.is_(True))
            .where(VatRateModel.is_active.is_(True))
        )
        if business_unit_id is not None:
            statement = statement.where(ProductModel.business_unit_id == business_unit_id)

        rates: dict[str, Decimal] = {}
        name_rates: dict[str, set[Decimal]] = defaultdict(set)
        for product, rate_percent in self._session.execute(statement).all():
            rate = Decimal(rate_percent)
            rates[str(product.id)] = rate
            if product.sku:
                rates[product.sku] = rate
                rates[product.sku.casefold()] = rate
            if product.name:
                name_rates[product.name].add(rate)
                name_rates[product.name.casefold()].add(rate)

        for name, candidate_rates in name_rates.items():
            if len(candidate_rates) == 1:
                rates[name] = next(iter(candidate_rates))

        return rates

    def _build_vat_readiness(
        self,
        *,
        rows: list[ImportRowModel],
        start_at: datetime,
        end_at: datetime,
        product_vat_rates: dict[str, Decimal],
    ) -> DashboardVatReadiness:
        gross_revenue = Decimal("0")
        covered_gross_revenue = Decimal("0")
        total_row_count = 0
        covered_row_count = 0

        for row in rows:
            payload = row.normalized_payload or {}
            occurred_at = self._payload_occurred_at(payload)
            if occurred_at is None or occurred_at < start_at or occurred_at > end_at:
                continue

            gross_amount = self._parse_decimal(payload.get("gross_amount"))
            gross_revenue += gross_amount
            total_row_count += 1
            if lookup_payload_vat_rate(payload, product_vat_rates) is not None:
                covered_gross_revenue += gross_amount
                covered_row_count += 1

        missing_row_count = total_row_count - covered_row_count
        missing_gross_revenue = gross_revenue - covered_gross_revenue
        coverage_percent = (
            (covered_gross_revenue / gross_revenue * Decimal("100")).quantize(
                Decimal("0.01")
            )
            if gross_revenue > Decimal("0")
            else Decimal("0.00")
        )

        if total_row_count == 0:
            status = "no_data"
        elif covered_row_count == total_row_count:
            status = "complete"
        elif covered_row_count == 0:
            status = "missing"
        else:
            status = "partial"

        return DashboardVatReadiness(
            status=status,
            coverage_percent=coverage_percent,
            gross_revenue=gross_revenue,
            covered_gross_revenue=covered_gross_revenue,
            missing_gross_revenue=missing_gross_revenue,
            total_row_count=total_row_count,
            covered_row_count=covered_row_count,
            missing_row_count=missing_row_count,
            source_layer="import_derived",
            amount_basis="gross",
            tax_breakdown_source=tax_breakdown_source(
                tax_count=covered_row_count,
                total_count=total_row_count,
            ),
        )

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

    def _build_traffic_heatmap(
        self,
        *,
        rows: list[ImportRowModel],
        start_at: datetime,
        end_at: datetime,
    ) -> list[DashboardHeatmapCell]:
        aggregate: dict[tuple[int, int], dict[str, Decimal | int]] = {
            (weekday, hour): {"revenue": Decimal("0"), "count": 0}
            for weekday in range(7)
            for hour in range(24)
        }

        for row in rows:
            payload = row.normalized_payload or {}
            occurred_at = self._payload_occurred_at(payload)
            if occurred_at is None or occurred_at < start_at or occurred_at > end_at:
                continue

            key = (occurred_at.weekday(), occurred_at.hour)
            aggregate[key]["revenue"] += self._parse_decimal(payload.get("gross_amount"))
            aggregate[key]["count"] += 1

        return [
            DashboardHeatmapCell(
                weekday=weekday,
                hour=hour,
                revenue=Decimal(aggregate[(weekday, hour)]["revenue"]),
                transaction_count=int(aggregate[(weekday, hour)]["count"]),
                source_layer="import_derived",
            )
            for weekday in range(7)
            for hour in range(24)
        ]

    def _build_category_trends(
        self,
        *,
        rows: list[ImportRowModel],
        start_at: datetime,
        end_at: datetime,
        limit: int,
    ) -> list[DashboardCategoryTrendRow]:
        period_length = end_at - start_at
        previous_end_at = start_at - timedelta(microseconds=1)
        previous_start_at = previous_end_at - period_length
        current = self._aggregate_categories(
            rows=rows,
            start_at=start_at,
            end_at=end_at,
        )
        previous = self._aggregate_categories(
            rows=rows,
            start_at=previous_start_at,
            end_at=previous_end_at,
        )

        labels = set(current) | set(previous)
        trend_rows = [
            self._build_category_trend_row(
                label=label,
                current=current.get(label, self._empty_category_aggregate()),
                previous=previous.get(label, self._empty_category_aggregate()),
            )
            for label in labels
        ]
        return sorted(
            trend_rows,
            key=lambda row: (abs(row.revenue_change), row.current_revenue),
            reverse=True,
        )[:limit]

    def _build_category_trend_row(
        self,
        *,
        label: str,
        current: dict[str, Decimal | int],
        previous: dict[str, Decimal | int],
    ) -> DashboardCategoryTrendRow:
        current_revenue = Decimal(current["revenue"])
        previous_revenue = Decimal(previous["revenue"])
        revenue_change = current_revenue - previous_revenue
        if previous_revenue > Decimal("0"):
            revenue_change_percent = revenue_change / previous_revenue * Decimal("100")
        elif current_revenue > Decimal("0"):
            revenue_change_percent = Decimal("100")
        else:
            revenue_change_percent = Decimal("0")

        return DashboardCategoryTrendRow(
            label=label,
            current_revenue=current_revenue,
            previous_revenue=previous_revenue,
            revenue_change=revenue_change,
            revenue_change_percent=revenue_change_percent,
            current_quantity=Decimal(current["quantity"]),
            previous_quantity=Decimal(previous["quantity"]),
            current_transaction_count=int(current["count"]),
            previous_transaction_count=int(previous["count"]),
            source_layer="import_derived",
        )

    def _aggregate_categories(
        self,
        *,
        rows: list[ImportRowModel],
        start_at: datetime,
        end_at: datetime,
    ) -> dict[str, dict[str, Decimal | int]]:
        aggregate: dict[str, dict[str, Decimal | int]] = defaultdict(
            self._empty_category_aggregate
        )

        for row in rows:
            payload = row.normalized_payload or {}
            occurred_at = self._payload_occurred_at(payload)
            if occurred_at is None or occurred_at < start_at or occurred_at > end_at:
                continue

            label = self._extract_text(
                payload.get("category_name"),
                fallback=UNKNOWN_CATEGORY,
            )
            aggregate[label]["revenue"] += self._parse_decimal(payload.get("gross_amount"))
            aggregate[label]["quantity"] += self._parse_decimal(payload.get("quantity"))
            aggregate[label]["count"] += 1

        return dict(aggregate)

    @staticmethod
    def _empty_category_aggregate() -> dict[str, Decimal | int]:
        return {"revenue": Decimal("0"), "quantity": Decimal("0"), "count": 0}

    def _build_product_risks(
        self,
        *,
        business_unit_id: uuid.UUID | None,
        limit: int,
    ) -> list[DashboardProductRiskRow]:
        product_statement = (
            select(ProductModel, CategoryModel.name)
            .outerjoin(CategoryModel, ProductModel.category_id == CategoryModel.id)
            .where(ProductModel.is_active.is_(True))
            .order_by(ProductModel.name.asc())
        )
        if business_unit_id is not None:
            product_statement = product_statement.where(
                ProductModel.business_unit_id == business_unit_id
            )

        latest_item_costs = self._build_latest_inventory_item_costs()
        recipe_costs = self._build_recipe_product_unit_costs(latest_item_costs)
        recipe_ingredients = self._build_active_recipe_ingredients(
            business_unit_id=business_unit_id
        )
        stock_levels = self._build_inventory_stock_level_summary(
            business_unit_id=business_unit_id
        )

        risk_rows: list[tuple[int, DashboardProductRiskRow]] = []
        for product, category_name in self._session.execute(product_statement).all():
            sale_price = Decimal(product.sale_price_gross or 0)
            unit_cost = recipe_costs.get(product.id)
            if unit_cost is None and product.default_unit_cost is not None:
                unit_cost = Decimal(product.default_unit_cost)
            if unit_cost is None:
                unit_cost = Decimal("0")

            margin_amount = sale_price - unit_cost
            margin_percent = (
                margin_amount / sale_price * Decimal("100")
                if sale_price > Decimal("0")
                else Decimal("0")
            )
            ingredients = recipe_ingredients.get(product.id, [])
            low_stock_count = 0
            missing_stock_count = 0
            reasons: list[str] = []
            score = 0

            if margin_amount < Decimal("0"):
                reasons.append("Negatív árrés")
                score += 100
            elif margin_percent > Decimal("0") and margin_percent < Decimal("15"):
                reasons.append("Alacsony árrés")
                score += 45

            if product.sale_price_gross is None:
                reasons.append("Hiányzó eladási ár")
                score += 60

            if product.id in recipe_costs and len(ingredients) == 0:
                reasons.append("Hiányzó receptsor")
                score += 55
            elif product.default_unit_cost is None and product.id not in recipe_costs:
                reasons.append("Hiányzó költségalap")
                score += 50

            for ingredient in ingredients:
                stock_level = stock_levels.get(ingredient.inventory_item_id)
                if stock_level is None or stock_level["movement_count"] == 0:
                    missing_stock_count += 1
                    continue
                if Decimal(stock_level["current_quantity"]) <= Decimal("0"):
                    low_stock_count += 1

            if low_stock_count > 0:
                reasons.append("Alapanyaghiány")
                score += 80 + low_stock_count * 5
            if missing_stock_count > 0:
                reasons.append("Hiányzó készletadat")
                score += 35 + missing_stock_count * 3

            if not reasons:
                continue

            risk_level = "danger" if score >= 80 else "warning"
            risk_rows.append(
                (
                    score,
                    DashboardProductRiskRow(
                        product_id=product.id,
                        product_name=product.name,
                        category_name=category_name or UNKNOWN_CATEGORY,
                        sale_price_gross=sale_price,
                        estimated_unit_cost=unit_cost,
                        estimated_margin_amount=margin_amount,
                        estimated_margin_percent=margin_percent,
                        risk_level=risk_level,
                        risk_reasons=tuple(reasons),
                        low_stock_ingredient_count=low_stock_count,
                        missing_stock_ingredient_count=missing_stock_count,
                        source_layer="catalog_inventory_actual",
                    ),
                )
            )

        return [
            row
            for _score, row in sorted(
                risk_rows,
                key=lambda item: (
                    item[0],
                    abs(item[1].estimated_margin_amount),
                    item[1].product_name,
                ),
                reverse=True,
            )[:limit]
        ]

    def _build_active_recipe_ingredients(
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
            statement = statement.where(ProductModel.business_unit_id == business_unit_id)

        ingredients_by_product: dict[uuid.UUID, list[RecipeIngredientModel]] = defaultdict(list)
        for product_id, ingredient in self._session.execute(statement).all():
            if ingredient is not None:
                ingredients_by_product[product_id].append(ingredient)
            else:
                ingredients_by_product.setdefault(product_id, [])
        return dict(ingredients_by_product)

    def _build_inventory_stock_level_summary(
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
            (InventoryMovementModel.movement_type == "waste", -InventoryMovementModel.quantity),
            else_=0,
        )
        statement = (
            select(
                InventoryItemModel.id,
                sa.func.coalesce(sa.func.sum(signed_quantity), 0).label("current_quantity"),
                sa.func.count(InventoryMovementModel.id).label("movement_count"),
                sa.func.max(InventoryMovementModel.occurred_at).label("last_movement_at"),
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
            statement = statement.where(InventoryItemModel.business_unit_id == business_unit_id)

        return {
            item_id: {
                "current_quantity": Decimal(current_quantity),
                "movement_count": int(movement_count),
                "last_movement_at": last_movement_at,
            }
            for item_id, current_quantity, movement_count, last_movement_at in self._session.execute(
                statement
            ).all()
        }

    def _build_stock_risks(
        self,
        *,
        business_unit_id: uuid.UUID | None,
        limit: int,
    ) -> list[DashboardStockRiskRow]:
        stock_levels = self._build_inventory_stock_level_summary(
            business_unit_id=business_unit_id
        )
        usage_counts = self._build_inventory_item_usage_counts(
            business_unit_id=business_unit_id
        )
        item_statement = (
            select(InventoryItemModel)
            .where(InventoryItemModel.is_active.is_(True))
            .where(InventoryItemModel.track_stock.is_(True))
            .order_by(InventoryItemModel.name.asc())
        )
        if business_unit_id is not None:
            item_statement = item_statement.where(
                InventoryItemModel.business_unit_id == business_unit_id
            )

        risk_rows: list[tuple[int, DashboardStockRiskRow]] = []
        for item in self._session.scalars(item_statement).all():
            stock_level = stock_levels.get(item.id)
            current_quantity = (
                Decimal(stock_level["current_quantity"])
                if stock_level is not None
                else Decimal("0")
            )
            movement_count = (
                int(stock_level["movement_count"]) if stock_level is not None else 0
            )
            used_by_product_count = usage_counts.get(item.id, 0)
            reasons: list[str] = []
            score = 0

            if movement_count == 0:
                reasons.append("Nincs készletmozgás")
                score += 55
            if current_quantity <= Decimal("0"):
                reasons.append("Nincs tényleges készlet")
                score += 90
            elif used_by_product_count > 0 and current_quantity <= Decimal(
                used_by_product_count
            ):
                reasons.append("Alacsony készlet recept-használathoz képest")
                score += 45
            if item.estimated_stock_quantity is None:
                reasons.append("Hiányzó becsült készlet")
                score += 25
            elif Decimal(item.estimated_stock_quantity) <= Decimal("0"):
                reasons.append("Becsült készlet nulla")
                score += 35
            if used_by_product_count > 0:
                score += min(used_by_product_count * 4, 24)

            if not reasons:
                continue

            risk_level = "danger" if score >= 80 else "warning"
            risk_rows.append(
                (
                    score,
                    DashboardStockRiskRow(
                        inventory_item_id=item.id,
                        item_name=item.name,
                        item_type=item.item_type,
                        current_quantity=current_quantity,
                        theoretical_quantity=None,
                        variance_quantity=None,
                        used_by_product_count=used_by_product_count,
                        movement_count=movement_count,
                        last_movement_at=(
                            stock_level["last_movement_at"]
                            if stock_level is not None
                            else None
                        ),
                        risk_level=risk_level,
                        risk_reasons=tuple(reasons),
                        source_layer="inventory_actual",
                    ),
                )
            )

        return [
            row
            for _score, row in sorted(
                risk_rows,
                key=lambda item: (
                    item[0],
                    item[1].used_by_product_count,
                    item[1].item_name,
                ),
                reverse=True,
            )[:limit]
        ]

    def _build_inventory_item_usage_counts(
        self,
        *,
        business_unit_id: uuid.UUID | None,
    ) -> dict[uuid.UUID, int]:
        statement = (
            select(
                RecipeIngredientModel.inventory_item_id,
                sa.func.count(sa.func.distinct(ProductModel.id)).label("product_count"),
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
            statement = statement.where(ProductModel.business_unit_id == business_unit_id)

        return {
            inventory_item_id: int(product_count)
            for inventory_item_id, product_count in self._session.execute(statement).all()
        }

    @staticmethod
    def _iter_buckets(
        *,
        start_at: datetime,
        end_at: datetime,
        grain: str,
    ) -> list[datetime]:
        buckets: list[datetime] = []
        current = SqlAlchemyAnalyticsRepository._bucket_datetime(start_at, grain=grain)
        end_bucket = SqlAlchemyAnalyticsRepository._bucket_datetime(end_at, grain=grain)
        while current <= end_bucket:
            buckets.append(current)
            if grain == "month":
                current = (
                    current.replace(year=current.year + 1, month=1)
                    if current.month == 12
                    else current.replace(month=current.month + 1)
                )
            elif grain == "hour":
                current += timedelta(hours=1)
            else:
                current += timedelta(days=1)
        return buckets

    @staticmethod
    def _bucket_datetime(value: datetime, *, grain: str) -> datetime:
        local_value = (
            value.replace(tzinfo=APP_TIME_ZONE)
            if value.tzinfo is None
            else value.astimezone(APP_TIME_ZONE)
        )
        if grain == "month":
            return local_value.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if grain == "hour":
            return local_value.replace(minute=0, second=0, microsecond=0)
        return local_value.replace(hour=0, minute=0, second=0, microsecond=0)

    @staticmethod
    def _as_app_time(value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=APP_TIME_ZONE)
        return value.astimezone(APP_TIME_ZONE)

    @staticmethod
    def _parse_payload_date(value: Any) -> date | None:
        if not isinstance(value, str):
            return None
        try:
            return date.fromisoformat(value)
        except ValueError:
            return None

    @staticmethod
    def _payload_occurred_at(payload: dict[str, Any]) -> datetime | None:
        occurred_at = payload.get("occurred_at")
        if isinstance(occurred_at, str):
            try:
                parsed = datetime.fromisoformat(occurred_at)
            except ValueError:
                parsed = None
            if parsed is not None:
                if parsed.tzinfo is None:
                    return parsed.replace(tzinfo=APP_TIME_ZONE)
                return parsed.astimezone(APP_TIME_ZONE)

        payload_date = SqlAlchemyAnalyticsRepository._parse_payload_date(
            payload.get("date")
        )
        if payload_date is None:
            return None
        return datetime(
            payload_date.year,
            payload_date.month,
            payload_date.day,
            tzinfo=APP_TIME_ZONE,
        )

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
        return cls._lookup_payload_unit_cost_optional(payload, product_costs) or Decimal("0")

    @staticmethod
    def _lookup_payload_unit_cost_optional(
        payload: dict[str, Any],
        product_costs: dict[str, Decimal],
    ) -> Decimal | None:
        for key_name in ("product_id", "sku", "product_name"):
            value = payload.get(key_name)
            if isinstance(value, str) and value in product_costs:
                return product_costs[value]
        return None

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
