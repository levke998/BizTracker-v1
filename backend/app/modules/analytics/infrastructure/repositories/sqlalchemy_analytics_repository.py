"""SQLAlchemy analytics read-model repository."""

from __future__ import annotations

import uuid
from collections import defaultdict
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.analytics.domain.entities.dashboard_snapshot import (
    DashboardBasketPairRow,
    DashboardBasketReceipt,
    DashboardBreakdownRow,
    DashboardExpenseDetailRow,
    DashboardExpenseSource,
    DashboardKpi,
    DashboardPeriod,
    DashboardPosSourceRow,
    DashboardProductDetailRow,
    DashboardSnapshot,
    DashboardVatReadiness,
)
from app.modules.analytics.infrastructure.repositories.expense_analytics_reader import (
    ExpenseAnalyticsReader,
)
from app.modules.analytics.infrastructure.repositories.catalog_inventory_risk_reader import (
    CatalogInventoryRiskReader,
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
from app.modules.analytics.infrastructure.repositories.statistics_analytics_builder import (
    DashboardStatisticsAnalyticsBuilder,
)
from app.modules.analytics.infrastructure.repositories.traffic_trend_analytics_builder import (
    TrafficTrendAnalyticsBuilder,
)
from app.modules.analytics.infrastructure.repositories.weather_analytics_reader import (
    WeatherAnalyticsReader,
)
from app.modules.finance.infrastructure.orm.transaction_model import (
    FinancialTransactionModel,
)
from app.modules.imports.infrastructure.orm.import_batch_model import ImportBatchModel
from app.modules.imports.infrastructure.orm.import_row_model import ImportRowModel
from app.modules.master_data.infrastructure.orm.business_unit_model import (
    BusinessUnitModel,
)
from app.modules.master_data.infrastructure.orm.product_model import ProductModel
from app.modules.master_data.infrastructure.orm.vat_rate_model import VatRateModel
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
        self._traffic_trends = TrafficTrendAnalyticsBuilder(
            time_zone=APP_TIME_ZONE,
            unknown_category=UNKNOWN_CATEGORY,
        )
        self._statistics = DashboardStatisticsAnalyticsBuilder(time_zone=APP_TIME_ZONE)
        self._expenses = ExpenseAnalyticsReader(session)
        self._catalog_inventory = CatalogInventoryRiskReader(
            session,
            unknown_category=UNKNOWN_CATEGORY,
        )
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
        product_costs = self._catalog_inventory.product_unit_costs(
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
                self._traffic_trends.build_heatmap(
                    rows=import_rows,
                    start_at=start_at,
                    end_at=end_at,
                )
            ),
            category_trends=tuple(
                self._traffic_trends.build_category_trends(
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
                    recipe_ingredients=self._catalog_inventory.active_recipe_ingredients(
                        business_unit_id=resolved_business_unit_id,
                    ),
                    stock_levels=self._catalog_inventory.stock_levels(
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
                self._catalog_inventory.build_product_risks(
                    business_unit_id=resolved_business_unit_id,
                    limit=8,
                )
            ),
            stock_risks=tuple(
                self._catalog_inventory.build_stock_risks(
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
            statistics_quality=self._statistics.build_quality(
                rows=import_rows,
                start_at=start_at,
                end_at=end_at,
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
            product_costs=self._catalog_inventory.product_unit_costs(
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
            select(BusinessUnitModel).where(
                BusinessUnitModel.code == business_unit_code
            )
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
            statement = statement.where(
                ImportBatchModel.business_unit_id == business_unit_id
            )

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
            statement = statement.where(
                ProductModel.business_unit_id == business_unit_id
            )

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
