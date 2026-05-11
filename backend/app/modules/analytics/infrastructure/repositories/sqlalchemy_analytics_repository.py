"""SQLAlchemy analytics read-model repository."""

from __future__ import annotations

import uuid
from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from itertools import combinations
from typing import Any
from zoneinfo import ZoneInfo

import sqlalchemy as sa
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.analytics.domain.entities.dashboard_snapshot import (
    DashboardBasketPairRow,
    DashboardBasketReceipt,
    DashboardBasketReceiptLine,
    DashboardBreakdownRow,
    DashboardCategoryTrendRow,
    DashboardExpenseDetailRow,
    DashboardExpenseRow,
    DashboardExpenseSource,
    DashboardExpenseSourceLine,
    DashboardFlowForecastEventRow,
    DashboardForecastCategoryDemandRow,
    DashboardForecastImpactRow,
    DashboardForecastPeakTimeRow,
    DashboardForecastPreparationRow,
    DashboardForecastProductDemandRow,
    DashboardHeatmapCell,
    DashboardKpi,
    DashboardPeriod,
    DashboardProductRiskRow,
    DashboardPosSourceRow,
    DashboardProductDetailRow,
    DashboardSnapshot,
    DashboardStockRiskRow,
    DashboardTemperatureBandInsightRow,
    DashboardTrendPoint,
    DashboardVatReadiness,
    DashboardWeatherCategoryInsightRow,
    DashboardWeatherConditionInsightRow,
)
from app.modules.finance.infrastructure.orm.transaction_model import (
    FinancialTransactionModel,
)
from app.modules.finance.application.services.vat_calculator import VatCalculator
from app.modules.events.infrastructure.orm.event_model import EventModel
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
from app.modules.procurement.infrastructure.orm.supplier_model import SupplierModel
from app.modules.production.infrastructure.orm.recipe_model import (
    RecipeIngredientModel,
    RecipeModel,
    RecipeVersionModel,
)
from app.modules.weather.application.commands.sync_shared_weather import (
    SHARED_WEATHER_LOCATION_NAME,
    SHARED_WEATHER_PROVIDER,
)
from app.modules.weather.infrastructure.orm.weather_model import (
    WeatherForecastHourlyModel,
    WeatherLocationModel,
    WeatherObservationHourlyModel,
)

BUSINESS_SCOPE_CODES = {
    "flow": "flow",
    "gourmand": "gourmand",
}
UNKNOWN_CATEGORY = "Kategória nélkül"
UNKNOWN_PRODUCT = "Ismeretlen termék"
SUPPLIER_INVOICE_SOURCE_TYPE = "supplier_invoice"
APP_TIME_ZONE = ZoneInfo("Europe/Budapest")
FORECAST_IMPACT_DAYS = 7


@dataclass(frozen=True, slots=True)
class PosTaxBreakdown:
    """Derived VAT breakdown for a POS row based on product master data."""

    net_amount: Decimal | None
    vat_amount: Decimal | None
    vat_rate_percent: Decimal | None
    source: str


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
        estimated_cogs = self._sum_estimated_cogs(
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
        average_basket_value, average_basket_quantity = self._build_basket_metrics(
            rows=import_rows,
            start_at=start_at,
            end_at=end_at,
        )
        forecast_category_demand_insights = tuple(
            self._build_forecast_category_demand_insights(
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
                self._build_trend(
                    transactions=transactions,
                    rows=import_rows,
                    product_costs=product_costs,
                    start_at=start_at,
                    end_at=end_at,
                    grain=grain,
                )
            ),
            category_breakdown=tuple(
                self._build_pos_breakdown(
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
                self._build_pos_breakdown(
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
                self._build_basket_value_distribution(
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
                self._build_weather_category_insights(
                    rows=import_rows,
                    start_at=start_at,
                    end_at=end_at,
                    limit=8,
                )
            ),
            temperature_band_insights=tuple(
                self._build_temperature_band_insights(
                    rows=import_rows,
                    start_at=start_at,
                    end_at=end_at,
                )
            ),
            weather_condition_insights=tuple(
                self._build_weather_condition_insights(
                    rows=import_rows,
                    start_at=start_at,
                    end_at=end_at,
                )
            ),
            forecast_impact_insights=tuple(
                self._build_forecast_impact_insights(
                    rows=import_rows,
                    scope=scope,
                )
            ),
            forecast_category_demand_insights=forecast_category_demand_insights,
            forecast_preparation_insights=tuple(
                self._build_forecast_preparation_insights(
                    business_unit_id=resolved_business_unit_id,
                    scope=scope,
                    demand_rows=list(forecast_category_demand_insights),
                    limit=10,
                )
            ),
            forecast_product_demand_insights=tuple(
                self._build_forecast_product_demand_insights(
                    rows=import_rows,
                    scope=scope,
                )
            ),
            forecast_peak_time_insights=tuple(
                self._build_forecast_peak_time_insights(
                    rows=import_rows,
                    scope=scope,
                )
            ),
            flow_forecast_event_insights=tuple(
                self._build_flow_forecast_event_insights(
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
                self._build_pos_breakdown(
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
                self._build_expense_breakdown(transactions=transactions, limit=10)
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
        return self._build_pos_breakdown(
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
        return self._build_product_detail_breakdown(
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
        return self._build_product_source_rows(
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
        expense_transactions = [
            transaction
            for transaction in transactions
            if transaction.direction == "outflow"
            and (
                transaction_type is None
                or transaction.transaction_type == transaction_type
            )
        ]
        tax_totals = self._build_supplier_invoice_tax_totals(
            [
                transaction.source_id
                for transaction in expense_transactions
                if transaction.source_type == SUPPLIER_INVOICE_SOURCE_TYPE
            ]
        )
        return [
            DashboardExpenseDetailRow(
                transaction_id=transaction.id,
                transaction_type=transaction.transaction_type,
                amount=Decimal(transaction.amount),
                gross_amount=Decimal(transaction.amount),
                net_amount=tax_totals.get(transaction.source_id, {}).get("net_amount"),
                vat_amount=tax_totals.get(transaction.source_id, {}).get("vat_amount"),
                currency=transaction.currency,
                occurred_at=transaction.occurred_at.date(),
                description=transaction.description,
                source_type=transaction.source_type,
                source_id=transaction.source_id,
                source_layer="financial_actual",
                amount_basis="gross",
                tax_breakdown_source=(
                    "supplier_invoice_actual"
                    if transaction.source_id in tax_totals
                    else "not_available"
                ),
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
                gross_amount=Decimal(transaction.amount),
                net_amount=None,
                vat_amount=None,
                currency=transaction.currency,
                occurred_at=transaction.occurred_at.date(),
                source_type=transaction.source_type,
                source_id=transaction.source_id,
                supplier_id=None,
                supplier_name=None,
                invoice_number=None,
                invoice_date=None,
                gross_total=None,
                net_total=None,
                vat_total=None,
                notes=None,
                amount_basis="gross",
                tax_breakdown_source="not_available",
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
                gross_amount=Decimal(transaction.amount),
                net_amount=None,
                vat_amount=None,
                currency=transaction.currency,
                occurred_at=transaction.occurred_at.date(),
                source_type=transaction.source_type,
                source_id=transaction.source_id,
                supplier_id=None,
                supplier_name=None,
                invoice_number=None,
                invoice_date=None,
                gross_total=None,
                net_total=None,
                vat_total=None,
                notes=None,
                amount_basis="gross",
                tax_breakdown_source="not_available",
                lines=(),
            )

        invoice, supplier_name = invoice_row
        lines = self._session.scalars(
            select(PurchaseInvoiceLineModel)
            .where(PurchaseInvoiceLineModel.invoice_id == invoice.id)
            .order_by(PurchaseInvoiceLineModel.description.asc())
        ).all()
        net_total = sum((Decimal(line.line_net_amount) for line in lines), Decimal("0"))
        vat_total = sum(
            (
                Decimal(line.vat_amount)
                for line in lines
                if line.vat_amount is not None
            ),
            Decimal("0"),
        )

        return DashboardExpenseSource(
            transaction_id=transaction.id,
            transaction_type=transaction.transaction_type,
            amount=Decimal(transaction.amount),
            gross_amount=Decimal(invoice.gross_total),
            net_amount=net_total,
            vat_amount=vat_total,
            currency=transaction.currency,
            occurred_at=transaction.occurred_at.date(),
            source_type=transaction.source_type,
            source_id=transaction.source_id,
            supplier_id=invoice.supplier_id,
            supplier_name=supplier_name,
            invoice_number=invoice.invoice_number,
            invoice_date=invoice.invoice_date,
            gross_total=Decimal(invoice.gross_total),
            net_total=net_total,
            vat_total=vat_total,
            notes=invoice.notes,
            amount_basis="gross",
            tax_breakdown_source="supplier_invoice_actual",
            lines=tuple(
                DashboardExpenseSourceLine(
                    line_id=line.id,
                    inventory_item_id=line.inventory_item_id,
                    description=line.description,
                    quantity=Decimal(line.quantity),
                    uom_id=line.uom_id,
                    unit_net_amount=Decimal(line.unit_net_amount),
                    line_net_amount=Decimal(line.line_net_amount),
                    vat_rate_id=line.vat_rate_id,
                    vat_amount=(
                        Decimal(line.vat_amount) if line.vat_amount is not None else None
                    ),
                    line_gross_amount=(
                        Decimal(line.line_gross_amount)
                        if line.line_gross_amount is not None
                        else None
                    ),
                )
                for line in lines
            ),
        )

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
        return self._build_basket_pairs(
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
        return self._build_basket_pair_receipts(
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

    def _calculate_payload_tax(
        self,
        payload: dict[str, Any],
        product_vat_rates: dict[str, Decimal],
    ) -> PosTaxBreakdown:
        rate_percent = self._lookup_payload_vat_rate(payload, product_vat_rates)
        if rate_percent is None:
            return PosTaxBreakdown(
                net_amount=None,
                vat_amount=None,
                vat_rate_percent=None,
                source="not_available",
            )

        gross_amount = self._parse_decimal(payload.get("gross_amount"))
        result = VatCalculator().calculate_from_gross(
            gross_amount=gross_amount,
            rate_percent=rate_percent,
        )
        return PosTaxBreakdown(
            net_amount=result.net_amount,
            vat_amount=result.vat_amount,
            vat_rate_percent=rate_percent,
            source="product_vat_derived",
        )

    def _lookup_payload_vat_rate(
        self,
        payload: dict[str, Any],
        product_vat_rates: dict[str, Decimal],
    ) -> Decimal | None:
        for key in self._payload_product_lookup_keys(payload):
            rate = product_vat_rates.get(key)
            if rate is not None:
                return rate
        return None

    @staticmethod
    def _payload_product_lookup_keys(payload: dict[str, Any]) -> tuple[str, ...]:
        keys: list[str] = []
        for key_name in ("product_id", "sku", "product_name"):
            value = payload.get(key_name)
            if isinstance(value, str) and value.strip():
                text = value.strip()
                keys.append(text)
                keys.append(text.casefold())
        return tuple(dict.fromkeys(keys))

    @staticmethod
    def _tax_breakdown_source(*, tax_count: int, total_count: int) -> str:
        if tax_count <= 0:
            return "not_available"
        if tax_count == total_count:
            return "product_vat_derived"
        return "partial_product_vat_derived"

    @staticmethod
    def _cost_source(*, cost_count: int, total_count: int) -> str:
        if cost_count <= 0:
            return "not_available"
        if cost_count == total_count:
            return "recipe_or_unit_cost"
        return "partial_recipe_or_unit_cost"

    @staticmethod
    def _margin_status(*, tax_count: int, cost_count: int, total_count: int) -> str:
        if total_count <= 0:
            return "no_data"
        has_complete_tax = tax_count == total_count
        has_complete_cost = cost_count == total_count
        if has_complete_tax and has_complete_cost:
            return "complete"
        if tax_count <= 0 and cost_count <= 0:
            return "missing_vat_and_cost"
        if tax_count <= 0:
            return "missing_vat_rate"
        if cost_count <= 0:
            return "missing_cost"
        return "partial"

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
            if self._lookup_payload_vat_rate(payload, product_vat_rates) is not None:
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
            tax_breakdown_source=self._tax_breakdown_source(
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

    def _sum_estimated_cogs(
        self,
        *,
        rows: list[ImportRowModel],
        product_costs: dict[str, Decimal],
        start_at: datetime,
        end_at: datetime,
    ) -> Decimal:
        total = Decimal("0")
        for row in rows:
            payload = row.normalized_payload or {}
            occurred_at = self._payload_occurred_at(payload)
            if occurred_at is None or occurred_at < start_at or occurred_at > end_at:
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
        start_at: datetime,
        end_at: datetime,
        grain: str,
    ) -> list[DashboardTrendPoint]:
        buckets = {
            bucket: {
                "revenue": Decimal("0"),
                "cost": Decimal("0"),
                "estimated_cogs": Decimal("0"),
            }
            for bucket in self._iter_buckets(start_at=start_at, end_at=end_at, grain=grain)
        }

        for transaction in transactions:
            bucket = self._bucket_datetime(transaction.occurred_at, grain=grain)
            if bucket not in buckets:
                continue

            if transaction.direction == "inflow":
                buckets[bucket]["revenue"] += Decimal(transaction.amount)
            elif transaction.direction == "outflow":
                buckets[bucket]["cost"] += Decimal(transaction.amount)

        for row in rows:
            payload = row.normalized_payload or {}
            occurred_at = self._payload_occurred_at(payload)
            if occurred_at is None or occurred_at < start_at or occurred_at > end_at:
                continue
            bucket = self._bucket_datetime(occurred_at, grain=grain)
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
        start_at: datetime,
        end_at: datetime,
        key_name: str,
        fallback: str,
        limit: int,
        product_vat_rates: dict[str, Decimal] | None = None,
    ) -> list[DashboardBreakdownRow]:
        aggregate: dict[str, dict[str, Decimal | int]] = defaultdict(
            lambda: {
                "revenue": Decimal("0"),
                "net_revenue": Decimal("0"),
                "vat_amount": Decimal("0"),
                "quantity": Decimal("0"),
                "count": 0,
                "tax_count": 0,
            }
        )
        vat_rates = product_vat_rates or {}

        for row in rows:
            payload = row.normalized_payload or {}
            occurred_at = self._payload_occurred_at(payload)
            if occurred_at is None or occurred_at < start_at or occurred_at > end_at:
                continue

            label = self._extract_text(payload.get(key_name), fallback=fallback)
            gross_amount = self._parse_decimal(payload.get("gross_amount"))
            tax = self._calculate_payload_tax(payload, vat_rates)
            aggregate[label]["revenue"] += gross_amount
            aggregate[label]["quantity"] += self._parse_decimal(payload.get("quantity"))
            aggregate[label]["count"] += 1
            if tax.net_amount is not None and tax.vat_amount is not None:
                aggregate[label]["net_revenue"] += tax.net_amount
                aggregate[label]["vat_amount"] += tax.vat_amount
                aggregate[label]["tax_count"] += 1

        sorted_rows = sorted(
            aggregate.items(),
            key=lambda item: Decimal(item[1]["revenue"]),
            reverse=True,
        )
        return [
            DashboardBreakdownRow(
                label=label,
                revenue=Decimal(values["revenue"]),
                net_revenue=(
                    Decimal(values["net_revenue"])
                    if int(values["tax_count"]) > 0
                    else None
                ),
                vat_amount=(
                    Decimal(values["vat_amount"])
                    if int(values["tax_count"]) > 0
                    else None
                ),
                quantity=Decimal(values["quantity"]),
                transaction_count=int(values["count"]),
                source_layer="import_derived",
                amount_basis="gross",
                tax_breakdown_source=self._tax_breakdown_source(
                    tax_count=int(values["tax_count"]),
                    total_count=int(values["count"]),
                ),
            )
            for label, values in sorted_rows[:limit]
        ]

    def _build_product_detail_breakdown(
        self,
        *,
        rows: list[ImportRowModel],
        start_at: datetime,
        end_at: datetime,
        category_name: str | None,
        limit: int,
        product_costs: dict[str, Decimal],
        product_vat_rates: dict[str, Decimal],
    ) -> list[DashboardProductDetailRow]:
        aggregate: dict[tuple[str, str], dict[str, Decimal | int]] = defaultdict(
            lambda: {
                "revenue": Decimal("0"),
                "net_revenue": Decimal("0"),
                "vat_amount": Decimal("0"),
                "estimated_cogs_net": Decimal("0"),
                "quantity": Decimal("0"),
                "count": 0,
                "tax_count": 0,
                "cost_count": 0,
            }
        )

        for row in rows:
            payload = row.normalized_payload or {}
            occurred_at = self._payload_occurred_at(payload)
            if occurred_at is None or occurred_at < start_at or occurred_at > end_at:
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
            gross_amount = self._parse_decimal(payload.get("gross_amount"))
            tax = self._calculate_payload_tax(payload, product_vat_rates)
            quantity = self._parse_decimal(payload.get("quantity"))
            unit_cost = self._lookup_payload_unit_cost_optional(payload, product_costs)
            aggregate[key]["revenue"] += gross_amount
            aggregate[key]["quantity"] += quantity
            aggregate[key]["count"] += 1
            if tax.net_amount is not None and tax.vat_amount is not None:
                aggregate[key]["net_revenue"] += tax.net_amount
                aggregate[key]["vat_amount"] += tax.vat_amount
                aggregate[key]["tax_count"] += 1
            if unit_cost is not None:
                aggregate[key]["estimated_cogs_net"] += unit_cost * quantity
                aggregate[key]["cost_count"] += 1

        sorted_rows = sorted(
            aggregate.items(),
            key=lambda item: Decimal(item[1]["revenue"]),
            reverse=True,
        )
        product_rows: list[DashboardProductDetailRow] = []
        for (product, category), values in sorted_rows[:limit]:
            tax_count = int(values["tax_count"])
            cost_count = int(values["cost_count"])
            total_count = int(values["count"])
            quantity = Decimal(values["quantity"])
            net_revenue = Decimal(values["net_revenue"]) if tax_count > 0 else None
            vat_amount = Decimal(values["vat_amount"]) if tax_count > 0 else None
            estimated_cogs = (
                Decimal(values["estimated_cogs_net"]) if cost_count > 0 else None
            )
            estimated_unit_cost = (
                estimated_cogs / quantity
                if estimated_cogs is not None and quantity > Decimal("0")
                else None
            )
            estimated_net_margin = (
                net_revenue - estimated_cogs
                if net_revenue is not None and estimated_cogs is not None
                else None
            )
            estimated_margin_percent = (
                estimated_net_margin / net_revenue * Decimal("100")
                if estimated_net_margin is not None
                and net_revenue is not None
                and net_revenue > Decimal("0")
                else None
            )

            product_rows.append(
                DashboardProductDetailRow(
                    product_name=product,
                    category_name=category,
                    revenue=Decimal(values["revenue"]),
                    net_revenue=net_revenue,
                    vat_amount=vat_amount,
                    estimated_unit_cost_net=estimated_unit_cost,
                    estimated_cogs_net=estimated_cogs,
                    estimated_net_margin_amount=estimated_net_margin,
                    estimated_margin_percent=estimated_margin_percent,
                    quantity=quantity,
                    transaction_count=total_count,
                    source_layer="import_derived",
                    amount_basis="gross",
                    tax_breakdown_source=self._tax_breakdown_source(
                        tax_count=tax_count,
                        total_count=total_count,
                    ),
                    cost_source=self._cost_source(
                        cost_count=cost_count,
                        total_count=total_count,
                    ),
                    margin_status=self._margin_status(
                        tax_count=tax_count,
                        cost_count=cost_count,
                        total_count=total_count,
                    ),
                )
            )

        return product_rows

    def _build_product_source_rows(
        self,
        *,
        rows: list[ImportRowModel],
        start_at: datetime,
        end_at: datetime,
        product_name: str,
        category_name: str | None,
        limit: int,
        product_vat_rates: dict[str, Decimal],
    ) -> list[DashboardPosSourceRow]:
        source_rows: list[DashboardPosSourceRow] = []
        for row in rows:
            payload = row.normalized_payload or {}
            occurred_at = self._payload_occurred_at(payload)
            if occurred_at is None or occurred_at < start_at or occurred_at > end_at:
                continue
            row_date = self._parse_payload_date(payload.get("date"))

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

            tax = self._calculate_payload_tax(payload, product_vat_rates)
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
                    net_amount=tax.net_amount,
                    vat_amount=tax.vat_amount,
                    vat_rate_percent=tax.vat_rate_percent,
                    payment_method=self._extract_optional_text(
                        payload.get("payment_method")
                    ),
                    source_layer="import_derived",
                    amount_basis="gross",
                    tax_breakdown_source=tax.source,
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
        start_at: datetime,
        end_at: datetime,
    ) -> tuple[Decimal, Decimal]:
        baskets: dict[str, dict[str, Decimal]] = defaultdict(
            lambda: {"gross_amount": Decimal("0"), "quantity": Decimal("0")}
        )

        for row in rows:
            payload = row.normalized_payload or {}
            occurred_at = self._payload_occurred_at(payload)
            if occurred_at is None or occurred_at < start_at or occurred_at > end_at:
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

    def _build_basket_value_distribution(
        self,
        *,
        rows: list[ImportRowModel],
        start_at: datetime,
        end_at: datetime,
    ) -> list[DashboardBreakdownRow]:
        baskets: dict[str, Decimal] = defaultdict(Decimal)

        for row in rows:
            payload = row.normalized_payload or {}
            occurred_at = self._payload_occurred_at(payload)
            if occurred_at is None or occurred_at < start_at or occurred_at > end_at:
                continue

            receipt_no = self._extract_optional_text(payload.get("receipt_no"))
            basket_key = receipt_no or str(row.id)
            baskets[basket_key] += self._parse_decimal(payload.get("gross_amount"))

        bands: list[tuple[str, Decimal | None, Decimal | None]] = [
            ("0-999", Decimal("0"), Decimal("999")),
            ("1000-2499", Decimal("1000"), Decimal("2499")),
            ("2500-4999", Decimal("2500"), Decimal("4999")),
            ("5000-9999", Decimal("5000"), Decimal("9999")),
            ("10000+", Decimal("10000"), None),
        ]
        aggregate: dict[str, dict[str, Decimal | int]] = {
            label: {"revenue": Decimal("0"), "count": 0} for label, _lower, _upper in bands
        }

        for amount in baskets.values():
            for label, lower, upper in bands:
                if lower is not None and amount < lower:
                    continue
                if upper is not None and amount > upper:
                    continue
                aggregate[label]["revenue"] += amount
                aggregate[label]["count"] += 1
                break

        return [
            DashboardBreakdownRow(
                label=label,
                revenue=Decimal(aggregate[label]["revenue"]),
                net_revenue=None,
                vat_amount=None,
                quantity=Decimal(aggregate[label]["count"]),
                transaction_count=int(aggregate[label]["count"]),
                source_layer="import_derived",
                amount_basis="gross",
                tax_breakdown_source="not_available",
            )
            for label, _lower, _upper in bands
        ]

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

    def _build_weather_category_insights(
        self,
        *,
        rows: list[ImportRowModel],
        start_at: datetime,
        end_at: datetime,
        limit: int,
    ) -> list[DashboardWeatherCategoryInsightRow]:
        observations = self._list_shared_weather_observations(
            start_at=start_at,
            end_at=end_at,
        )
        if not observations:
            return []

        weather_by_hour = {
            self._hour_start_utc(observation.observed_at): observation
            for observation in observations
        }
        aggregate: dict[tuple[str, str], dict[str, Decimal | int]] = defaultdict(
            lambda: {
                "revenue": Decimal("0"),
                "quantity": Decimal("0"),
                "count": 0,
                "temperature_sum": Decimal("0"),
                "temperature_count": 0,
            }
        )

        for row in rows:
            payload = row.normalized_payload or {}
            occurred_at = self._payload_occurred_at(payload)
            if occurred_at is None or occurred_at < start_at or occurred_at > end_at:
                continue

            observation = weather_by_hour.get(self._hour_start_utc(occurred_at))
            if observation is None:
                continue

            category_name = self._extract_text(
                payload.get("category_name"),
                fallback=UNKNOWN_CATEGORY,
            )
            key = (category_name, observation.weather_condition)
            aggregate[key]["revenue"] += self._parse_decimal(payload.get("gross_amount"))
            aggregate[key]["quantity"] += self._parse_decimal(payload.get("quantity"))
            aggregate[key]["count"] += 1
            if observation.temperature_c is not None:
                aggregate[key]["temperature_sum"] += Decimal(observation.temperature_c)
                aggregate[key]["temperature_count"] += 1

        insight_rows: list[DashboardWeatherCategoryInsightRow] = []
        for (category_name, weather_condition), values in aggregate.items():
            temperature_count = int(values["temperature_count"])
            average_temperature = (
                Decimal(values["temperature_sum"]) / Decimal(temperature_count)
                if temperature_count > 0
                else None
            )
            insight_rows.append(
                DashboardWeatherCategoryInsightRow(
                    category_name=category_name,
                    weather_condition=weather_condition,
                    revenue=Decimal(values["revenue"]),
                    quantity=Decimal(values["quantity"]),
                    transaction_count=int(values["count"]),
                    average_temperature_c=average_temperature,
                    source_layer="weather_enriched_import",
                )
            )

        return sorted(
            insight_rows,
            key=lambda item: (item.revenue, item.transaction_count),
            reverse=True,
        )[:limit]

    def _build_temperature_band_insights(
        self,
        *,
        rows: list[ImportRowModel],
        start_at: datetime,
        end_at: datetime,
    ) -> list[DashboardTemperatureBandInsightRow]:
        observations = self._list_shared_weather_observations(
            start_at=start_at,
            end_at=end_at,
        )
        if not observations:
            return []

        weather_by_hour = {
            self._hour_start_utc(observation.observed_at): observation
            for observation in observations
        }
        aggregate: dict[str, dict[str, Any]] = defaultdict(
            lambda: {
                "revenue": Decimal("0"),
                "quantity": Decimal("0"),
                "count": 0,
                "baskets": defaultdict(Decimal),
                "temperature_sum": Decimal("0"),
                "temperature_count": 0,
                "categories": defaultdict(Decimal),
            }
        )

        for row in rows:
            payload = row.normalized_payload or {}
            occurred_at = self._payload_occurred_at(payload)
            if occurred_at is None or occurred_at < start_at or occurred_at > end_at:
                continue

            observation = weather_by_hour.get(self._hour_start_utc(occurred_at))
            if observation is None or observation.temperature_c is None:
                continue

            temperature = Decimal(observation.temperature_c)
            band = self._temperature_band(temperature)
            revenue = self._parse_decimal(payload.get("gross_amount"))
            quantity = self._parse_decimal(payload.get("quantity"))
            category_name = self._extract_text(
                payload.get("category_name"),
                fallback=UNKNOWN_CATEGORY,
            )
            receipt_key = self._extract_text(
                payload.get("receipt_no"),
                fallback=f"row-{row.id}",
            )

            aggregate[band]["revenue"] += revenue
            aggregate[band]["quantity"] += quantity
            aggregate[band]["count"] += 1
            aggregate[band]["baskets"][receipt_key] += revenue
            aggregate[band]["temperature_sum"] += temperature
            aggregate[band]["temperature_count"] += 1
            aggregate[band]["categories"][category_name] += revenue

        band_order = {"hideg": 0, "enyhe": 1, "meleg": 2, "kanikula": 3}
        insight_rows: list[DashboardTemperatureBandInsightRow] = []
        for band, values in aggregate.items():
            baskets = dict(values["baskets"])
            categories = dict(values["categories"])
            basket_count = len(baskets)
            temperature_count = int(values["temperature_count"])
            top_category_name = UNKNOWN_CATEGORY
            top_category_revenue = Decimal("0")
            if categories:
                top_category_name, top_category_revenue = max(
                    categories.items(),
                    key=lambda item: item[1],
                )

            revenue = Decimal(values["revenue"])
            insight_rows.append(
                DashboardTemperatureBandInsightRow(
                    temperature_band=band,
                    revenue=revenue,
                    quantity=Decimal(values["quantity"]),
                    transaction_count=int(values["count"]),
                    basket_count=basket_count,
                    average_basket_value=(
                        revenue / Decimal(basket_count)
                        if basket_count > 0
                        else Decimal("0")
                    ),
                    average_temperature_c=(
                        Decimal(values["temperature_sum"]) / Decimal(temperature_count)
                        if temperature_count > 0
                        else None
                    ),
                    top_category_name=top_category_name,
                    top_category_revenue=Decimal(top_category_revenue),
                    source_layer="weather_enriched_import",
                )
            )

        return sorted(
            insight_rows,
            key=lambda row: band_order.get(row.temperature_band, 99),
        )

    def _build_weather_condition_insights(
        self,
        *,
        rows: list[ImportRowModel],
        start_at: datetime,
        end_at: datetime,
    ) -> list[DashboardWeatherConditionInsightRow]:
        observations = self._list_shared_weather_observations(
            start_at=start_at,
            end_at=end_at,
        )
        if not observations:
            return []

        weather_by_hour = {
            self._hour_start_utc(observation.observed_at): observation
            for observation in observations
        }
        aggregate: dict[str, dict[str, Any]] = defaultdict(
            lambda: {
                "revenue": Decimal("0"),
                "quantity": Decimal("0"),
                "count": 0,
                "baskets": defaultdict(Decimal),
                "cloud_sum": Decimal("0"),
                "cloud_count": 0,
                "precipitation_sum": Decimal("0"),
                "categories": defaultdict(Decimal),
            }
        )

        for row in rows:
            payload = row.normalized_payload or {}
            occurred_at = self._payload_occurred_at(payload)
            if occurred_at is None or occurred_at < start_at or occurred_at > end_at:
                continue

            observation = weather_by_hour.get(self._hour_start_utc(occurred_at))
            if observation is None:
                continue

            condition = self._weather_condition_band(observation)
            revenue = self._parse_decimal(payload.get("gross_amount"))
            quantity = self._parse_decimal(payload.get("quantity"))
            category_name = self._extract_text(
                payload.get("category_name"),
                fallback=UNKNOWN_CATEGORY,
            )
            receipt_key = self._extract_text(
                payload.get("receipt_no"),
                fallback=f"row-{row.id}",
            )

            aggregate[condition]["revenue"] += revenue
            aggregate[condition]["quantity"] += quantity
            aggregate[condition]["count"] += 1
            aggregate[condition]["baskets"][receipt_key] += revenue
            aggregate[condition]["precipitation_sum"] += self._observation_precipitation(
                observation
            )
            if observation.cloud_cover_percent is not None:
                aggregate[condition]["cloud_sum"] += Decimal(
                    observation.cloud_cover_percent
                )
                aggregate[condition]["cloud_count"] += 1
            aggregate[condition]["categories"][category_name] += revenue

        condition_order = {
            "napos_szaraz": 0,
            "reszben_felhos": 1,
            "borult": 2,
            "csapadekos": 3,
        }
        insight_rows: list[DashboardWeatherConditionInsightRow] = []
        for condition, values in aggregate.items():
            baskets = dict(values["baskets"])
            categories = dict(values["categories"])
            basket_count = len(baskets)
            cloud_count = int(values["cloud_count"])
            top_category_name = UNKNOWN_CATEGORY
            top_category_revenue = Decimal("0")
            if categories:
                top_category_name, top_category_revenue = max(
                    categories.items(),
                    key=lambda item: item[1],
                )

            revenue = Decimal(values["revenue"])
            insight_rows.append(
                DashboardWeatherConditionInsightRow(
                    condition_band=condition,
                    revenue=revenue,
                    quantity=Decimal(values["quantity"]),
                    transaction_count=int(values["count"]),
                    basket_count=basket_count,
                    average_basket_value=(
                        revenue / Decimal(basket_count)
                        if basket_count > 0
                        else Decimal("0")
                    ),
                    average_cloud_cover_percent=(
                        Decimal(values["cloud_sum"]) / Decimal(cloud_count)
                        if cloud_count > 0
                        else None
                    ),
                    precipitation_mm=Decimal(values["precipitation_sum"]),
                    top_category_name=top_category_name,
                    top_category_revenue=Decimal(top_category_revenue),
                    source_layer="weather_enriched_import",
                )
            )

        return sorted(
            insight_rows,
            key=lambda row: condition_order.get(row.condition_band, 99),
        )

    def _list_shared_weather_observations(
        self,
        *,
        start_at: datetime,
        end_at: datetime,
    ) -> list[WeatherObservationHourlyModel]:
        period_start = self._hour_start_utc(start_at)
        period_end = self._hour_start_utc(end_at)
        statement = (
            select(WeatherObservationHourlyModel)
            .join(
                WeatherLocationModel,
                WeatherObservationHourlyModel.weather_location_id == WeatherLocationModel.id,
            )
            .where(WeatherLocationModel.scope == "shared")
            .where(WeatherLocationModel.name == SHARED_WEATHER_LOCATION_NAME)
            .where(WeatherLocationModel.provider == SHARED_WEATHER_PROVIDER)
            .where(WeatherObservationHourlyModel.provider == SHARED_WEATHER_PROVIDER)
            .where(WeatherObservationHourlyModel.observed_at >= period_start)
            .where(WeatherObservationHourlyModel.observed_at <= period_end)
            .order_by(WeatherObservationHourlyModel.observed_at.asc())
        )
        return list(self._session.scalars(statement).all())

    def _build_forecast_impact_insights(
        self,
        *,
        rows: list[ImportRowModel],
        scope: str,
    ) -> list[DashboardForecastImpactRow]:
        now = datetime.now(APP_TIME_ZONE)
        forecast_rows = self._list_shared_weather_forecasts(
            start_at=now,
            end_at=now + timedelta(days=FORECAST_IMPACT_DAYS),
        )
        if not forecast_rows:
            return []

        historical_days = self._build_historical_weather_sales_days(rows=rows)
        if not historical_days:
            return []

        exact_baselines = self._average_revenue_by_key(
            historical_days,
            key_builder=lambda day: (
                day["temperature_band"],
                day["condition_band"],
            ),
        )
        weekday_baselines = self._average_revenue_by_key(
            historical_days,
            key_builder=lambda day: day["weekday"],
        )
        overall_average = self._average_decimal(
            [Decimal(day["revenue"]) for day in historical_days]
        )

        forecast_days = self._aggregate_forecast_days(forecast_rows)
        insights: list[DashboardForecastImpactRow] = []
        for forecast_date, values in sorted(forecast_days.items()):
            forecast_hours = int(values["hour_count"])
            if forecast_hours <= 0:
                continue

            temperature_average = self._average_decimal(
                [Decimal(value) for value in values["temperatures"]]
            )
            temperature_band = (
                self._temperature_band(temperature_average)
                if temperature_average is not None
                else "ismeretlen"
            )
            condition_band = self._dominant_label(
                values["condition_counts"],
                fallback="ismeretlen",
            )
            exact_key = (temperature_band, condition_band)

            if exact_key in exact_baselines:
                expected_revenue = exact_baselines[exact_key]
                confidence = "magas"
            elif forecast_date.weekday() in weekday_baselines:
                expected_revenue = weekday_baselines[forecast_date.weekday()]
                confidence = "kozepes"
            else:
                expected_revenue = overall_average or Decimal("0")
                confidence = "alacsony"

            if overall_average and overall_average > Decimal("0"):
                historical_average = overall_average
            else:
                historical_average = expected_revenue

            insights.append(
                DashboardForecastImpactRow(
                    forecast_date=forecast_date,
                    forecast_hours=forecast_hours,
                    dominant_temperature_band=temperature_band,
                    dominant_condition_band=condition_band,
                    average_temperature_c=temperature_average,
                    precipitation_mm=Decimal(values["precipitation_sum"]),
                    expected_revenue=expected_revenue,
                    historical_average_revenue=historical_average,
                    confidence=confidence,
                    recommendation=self._forecast_recommendation(
                        scope=scope,
                        temperature_band=temperature_band,
                        condition_band=condition_band,
                        expected_revenue=expected_revenue,
                        historical_average=historical_average,
                    ),
                    forecast_updated_at=values["latest_forecast_run_at"],
                    source_layer="weather_forecast_cache",
                )
            )

        return insights[:FORECAST_IMPACT_DAYS]

    def _build_forecast_category_demand_insights(
        self,
        *,
        rows: list[ImportRowModel],
        scope: str,
    ) -> list[DashboardForecastCategoryDemandRow]:
        if scope == "flow":
            return []

        now = datetime.now(APP_TIME_ZONE)
        forecast_rows = self._list_shared_weather_forecasts(
            start_at=now,
            end_at=now + timedelta(days=FORECAST_IMPACT_DAYS),
        )
        if not forecast_rows:
            return []

        historical_category_days = self._build_historical_weather_category_days(
            rows=rows,
        )
        if not historical_category_days:
            return []

        exact_baselines = self._average_category_sales_by_key(
            historical_category_days,
            key_builder=lambda day: (
                day["category_name"],
                day["temperature_band"],
                day["condition_band"],
            ),
        )
        weekday_baselines = self._average_category_sales_by_key(
            historical_category_days,
            key_builder=lambda day: (
                day["category_name"],
                day["weekday"],
            ),
        )
        category_baselines = self._average_category_sales_by_key(
            historical_category_days,
            key_builder=lambda day: day["category_name"],
        )

        forecast_days = self._aggregate_forecast_days(forecast_rows)
        rows_by_date: dict[date, list[DashboardForecastCategoryDemandRow]] = defaultdict(list)
        for forecast_date, values in sorted(forecast_days.items()):
            temperature_average = self._average_decimal(
                [Decimal(value) for value in values["temperatures"]]
            )
            temperature_band = (
                self._temperature_band(temperature_average)
                if temperature_average is not None
                else "ismeretlen"
            )
            condition_band = self._dominant_label(
                values["condition_counts"],
                fallback="ismeretlen",
            )

            for category_name, category_average in category_baselines.items():
                exact_key = (category_name, temperature_band, condition_band)
                weekday_key = (category_name, forecast_date.weekday())
                if exact_key in exact_baselines:
                    baseline = exact_baselines[exact_key]
                    confidence = "magas"
                elif weekday_key in weekday_baselines:
                    baseline = weekday_baselines[weekday_key]
                    confidence = "kozepes"
                else:
                    baseline = category_average
                    confidence = "alacsony"

                expected_revenue = Decimal(baseline["revenue"])
                expected_quantity = Decimal(baseline["quantity"])
                historical_average = Decimal(category_average["revenue"])
                uplift_percent = (
                    (expected_revenue - historical_average)
                    / historical_average
                    * Decimal("100")
                    if historical_average > Decimal("0")
                    else Decimal("0")
                )
                demand_signal = self._forecast_demand_signal(uplift_percent)

                rows_by_date[forecast_date].append(
                    DashboardForecastCategoryDemandRow(
                        forecast_date=forecast_date,
                        category_name=str(category_name),
                        dominant_temperature_band=temperature_band,
                        dominant_condition_band=condition_band,
                        expected_revenue=expected_revenue,
                        expected_quantity=expected_quantity,
                        historical_average_revenue=historical_average,
                        revenue_uplift_percent=uplift_percent,
                        confidence=confidence,
                        demand_signal=demand_signal,
                        recommendation=self._category_forecast_recommendation(
                            category_name=str(category_name),
                            temperature_band=temperature_band,
                            condition_band=condition_band,
                            demand_signal=demand_signal,
                        ),
                        source_layer="weather_forecast_category_model",
                    )
                )

        demand_rows: list[DashboardForecastCategoryDemandRow] = []
        for forecast_date in sorted(rows_by_date):
            ranked = sorted(
                rows_by_date[forecast_date],
                key=lambda row: (row.expected_revenue, row.expected_quantity),
                reverse=True,
            )
            demand_rows.extend(ranked[:3])

        return demand_rows[:18]

    def _build_historical_weather_sales_days(
        self,
        *,
        rows: list[ImportRowModel],
    ) -> list[dict[str, object]]:
        occurred_values = [
            occurred_at
            for row in rows
            if (occurred_at := self._payload_occurred_at(row.normalized_payload or {}))
            is not None
        ]
        if not occurred_values:
            return []

        observations = self._list_shared_weather_observations(
            start_at=min(occurred_values),
            end_at=max(occurred_values) + timedelta(hours=1),
        )
        if not observations:
            return []

        weather_by_hour = {
            self._hour_start_utc(observation.observed_at): observation
            for observation in observations
        }
        daily: dict[date, dict[str, Any]] = defaultdict(
            lambda: {
                "revenue": Decimal("0"),
                "temperatures": [],
                "precipitation_sum": Decimal("0"),
                "condition_counts": defaultdict(int),
            }
        )

        for row in rows:
            payload = row.normalized_payload or {}
            occurred_at = self._payload_occurred_at(payload)
            if occurred_at is None:
                continue

            observation = weather_by_hour.get(self._hour_start_utc(occurred_at))
            if observation is None:
                continue

            local_date = occurred_at.astimezone(APP_TIME_ZONE).date()
            daily[local_date]["revenue"] += self._parse_decimal(
                payload.get("gross_amount")
            )
            if observation.temperature_c is not None:
                daily[local_date]["temperatures"].append(
                    Decimal(observation.temperature_c)
                )
            daily[local_date]["precipitation_sum"] += self._observation_precipitation(
                observation
            )
            daily[local_date]["condition_counts"][
                self._weather_condition_band(observation)
            ] += 1

        historical_days: list[dict[str, object]] = []
        for local_date, values in daily.items():
            average_temperature = self._average_decimal(values["temperatures"])
            historical_days.append(
                {
                    "date": local_date,
                    "weekday": local_date.weekday(),
                    "revenue": Decimal(values["revenue"]),
                    "temperature_band": (
                        self._temperature_band(average_temperature)
                        if average_temperature is not None
                        else "ismeretlen"
                    ),
                    "condition_band": self._dominant_label(
                        values["condition_counts"],
                        fallback="ismeretlen",
                    ),
                }
            )

        return historical_days

    def _build_historical_weather_category_days(
        self,
        *,
        rows: list[ImportRowModel],
    ) -> list[dict[str, object]]:
        occurred_values = [
            occurred_at
            for row in rows
            if (occurred_at := self._payload_occurred_at(row.normalized_payload or {}))
            is not None
        ]
        if not occurred_values:
            return []

        observations = self._list_shared_weather_observations(
            start_at=min(occurred_values),
            end_at=max(occurred_values) + timedelta(hours=1),
        )
        if not observations:
            return []

        weather_by_hour = {
            self._hour_start_utc(observation.observed_at): observation
            for observation in observations
        }
        daily: dict[tuple[date, str], dict[str, Any]] = defaultdict(
            lambda: {
                "revenue": Decimal("0"),
                "quantity": Decimal("0"),
                "temperatures": [],
                "condition_counts": defaultdict(int),
            }
        )

        for row in rows:
            payload = row.normalized_payload or {}
            occurred_at = self._payload_occurred_at(payload)
            if occurred_at is None:
                continue

            observation = weather_by_hour.get(self._hour_start_utc(occurred_at))
            if observation is None:
                continue

            category_name = self._extract_text(
                payload.get("category_name"),
                fallback=UNKNOWN_CATEGORY,
            )
            local_date = occurred_at.astimezone(APP_TIME_ZONE).date()
            key = (local_date, category_name)
            daily[key]["revenue"] += self._parse_decimal(payload.get("gross_amount"))
            daily[key]["quantity"] += self._parse_decimal(payload.get("quantity"))
            if observation.temperature_c is not None:
                daily[key]["temperatures"].append(Decimal(observation.temperature_c))
            daily[key]["condition_counts"][
                self._weather_condition_band(observation)
            ] += 1

        category_days: list[dict[str, object]] = []
        for (local_date, category_name), values in daily.items():
            average_temperature = self._average_decimal(values["temperatures"])
            category_days.append(
                {
                    "date": local_date,
                    "weekday": local_date.weekday(),
                    "category_name": category_name,
                    "revenue": Decimal(values["revenue"]),
                    "quantity": Decimal(values["quantity"]),
                    "temperature_band": (
                        self._temperature_band(average_temperature)
                        if average_temperature is not None
                        else "ismeretlen"
                    ),
                    "condition_band": self._dominant_label(
                        values["condition_counts"],
                        fallback="ismeretlen",
                    ),
                }
            )

        return category_days

    def _build_forecast_product_demand_insights(
        self,
        *,
        rows: list[ImportRowModel],
        scope: str,
    ) -> list[DashboardForecastProductDemandRow]:
        if scope == "flow":
            return []

        now = datetime.now(APP_TIME_ZONE)
        forecast_rows = self._list_shared_weather_forecasts(
            start_at=now,
            end_at=now + timedelta(days=FORECAST_IMPACT_DAYS),
        )
        if not forecast_rows:
            return []

        historical_product_days = self._build_historical_weather_product_days(rows=rows)
        if not historical_product_days:
            return []

        exact_baselines = self._average_product_sales_by_key(
            historical_product_days,
            key_builder=lambda day: (
                day["product_name"],
                day["temperature_band"],
                day["condition_band"],
            ),
        )
        weekday_baselines = self._average_product_sales_by_key(
            historical_product_days,
            key_builder=lambda day: (
                day["product_name"],
                day["weekday"],
            ),
        )
        product_baselines = self._average_product_sales_by_key(
            historical_product_days,
            key_builder=lambda day: day["product_name"],
        )
        product_categories = self._dominant_product_categories(historical_product_days)

        rows_by_date: dict[date, list[DashboardForecastProductDemandRow]] = defaultdict(list)
        for forecast_date, values in sorted(self._aggregate_forecast_days(forecast_rows).items()):
            temperature_average = self._average_decimal(
                [Decimal(value) for value in values["temperatures"]]
            )
            temperature_band = (
                self._temperature_band(temperature_average)
                if temperature_average is not None
                else "ismeretlen"
            )
            condition_band = self._dominant_label(
                values["condition_counts"],
                fallback="ismeretlen",
            )

            for product_name, product_average in product_baselines.items():
                exact_key = (product_name, temperature_band, condition_band)
                weekday_key = (product_name, forecast_date.weekday())
                if exact_key in exact_baselines:
                    baseline = exact_baselines[exact_key]
                    confidence = "magas"
                elif weekday_key in weekday_baselines:
                    baseline = weekday_baselines[weekday_key]
                    confidence = "kozepes"
                else:
                    baseline = product_average
                    confidence = "alacsony"

                expected_revenue = Decimal(baseline["revenue"])
                expected_quantity = Decimal(baseline["quantity"])
                historical_average = Decimal(product_average["revenue"])
                uplift_percent = (
                    (expected_revenue - historical_average)
                    / historical_average
                    * Decimal("100")
                    if historical_average > Decimal("0")
                    else Decimal("0")
                )
                demand_signal = self._forecast_demand_signal(uplift_percent)

                rows_by_date[forecast_date].append(
                    DashboardForecastProductDemandRow(
                        forecast_date=forecast_date,
                        product_name=str(product_name),
                        category_name=product_categories.get(
                            str(product_name),
                            UNKNOWN_CATEGORY,
                        ),
                        dominant_temperature_band=temperature_band,
                        dominant_condition_band=condition_band,
                        expected_revenue=expected_revenue,
                        expected_quantity=expected_quantity,
                        historical_average_revenue=historical_average,
                        revenue_uplift_percent=uplift_percent,
                        confidence=confidence,
                        demand_signal=demand_signal,
                        recommendation=self._product_forecast_recommendation(
                            product_name=str(product_name),
                            demand_signal=demand_signal,
                            condition_band=condition_band,
                        ),
                        source_layer="weather_forecast_product_model",
                    )
                )

        product_rows: list[DashboardForecastProductDemandRow] = []
        for forecast_date in sorted(rows_by_date):
            ranked = sorted(
                rows_by_date[forecast_date],
                key=lambda row: (row.expected_revenue, row.expected_quantity),
                reverse=True,
            )
            product_rows.extend(ranked[:5])

        return product_rows[:30]

    def _build_historical_weather_product_days(
        self,
        *,
        rows: list[ImportRowModel],
    ) -> list[dict[str, object]]:
        occurred_values = [
            occurred_at
            for row in rows
            if (occurred_at := self._payload_occurred_at(row.normalized_payload or {}))
            is not None
        ]
        if not occurred_values:
            return []

        observations = self._list_shared_weather_observations(
            start_at=min(occurred_values),
            end_at=max(occurred_values) + timedelta(hours=1),
        )
        if not observations:
            return []

        weather_by_hour = {
            self._hour_start_utc(observation.observed_at): observation
            for observation in observations
        }
        daily: dict[tuple[date, str], dict[str, Any]] = defaultdict(
            lambda: {
                "category_counts": defaultdict(int),
                "revenue": Decimal("0"),
                "quantity": Decimal("0"),
                "temperatures": [],
                "condition_counts": defaultdict(int),
            }
        )

        for row in rows:
            payload = row.normalized_payload or {}
            occurred_at = self._payload_occurred_at(payload)
            if occurred_at is None:
                continue

            observation = weather_by_hour.get(self._hour_start_utc(occurred_at))
            if observation is None:
                continue

            product_name = self._extract_text(
                payload.get("product_name"),
                fallback=UNKNOWN_PRODUCT,
            )
            category_name = self._extract_text(
                payload.get("category_name"),
                fallback=UNKNOWN_CATEGORY,
            )
            local_date = occurred_at.astimezone(APP_TIME_ZONE).date()
            key = (local_date, product_name)
            daily[key]["category_counts"][category_name] += 1
            daily[key]["revenue"] += self._parse_decimal(payload.get("gross_amount"))
            daily[key]["quantity"] += self._parse_decimal(payload.get("quantity"))
            if observation.temperature_c is not None:
                daily[key]["temperatures"].append(Decimal(observation.temperature_c))
            daily[key]["condition_counts"][
                self._weather_condition_band(observation)
            ] += 1

        product_days: list[dict[str, object]] = []
        for (local_date, product_name), values in daily.items():
            average_temperature = self._average_decimal(values["temperatures"])
            product_days.append(
                {
                    "date": local_date,
                    "weekday": local_date.weekday(),
                    "product_name": product_name,
                    "category_name": self._dominant_label(
                        values["category_counts"],
                        fallback=UNKNOWN_CATEGORY,
                    ),
                    "revenue": Decimal(values["revenue"]),
                    "quantity": Decimal(values["quantity"]),
                    "temperature_band": (
                        self._temperature_band(average_temperature)
                        if average_temperature is not None
                        else "ismeretlen"
                    ),
                    "condition_band": self._dominant_label(
                        values["condition_counts"],
                        fallback="ismeretlen",
                    ),
                }
            )

        return product_days

    def _build_forecast_peak_time_insights(
        self,
        *,
        rows: list[ImportRowModel],
        scope: str,
    ) -> list[DashboardForecastPeakTimeRow]:
        if scope == "flow":
            return []

        now = datetime.now(APP_TIME_ZONE)
        forecast_rows = self._list_shared_weather_forecasts(
            start_at=now,
            end_at=now + timedelta(days=FORECAST_IMPACT_DAYS),
        )
        if not forecast_rows:
            return []

        historical_windows = self._build_historical_weather_time_windows(rows=rows)
        if not historical_windows:
            return []

        exact_baselines = self._average_window_sales_by_key(
            historical_windows,
            key_builder=lambda row: (
                row["time_window"],
                row["temperature_band"],
                row["condition_band"],
            ),
        )
        weekday_baselines = self._average_window_sales_by_key(
            historical_windows,
            key_builder=lambda row: (
                row["time_window"],
                row["weekday"],
            ),
        )
        window_baselines = self._average_window_sales_by_key(
            historical_windows,
            key_builder=lambda row: row["time_window"],
        )

        rows_by_date: dict[date, list[DashboardForecastPeakTimeRow]] = defaultdict(list)
        forecast_by_day_window = self._aggregate_forecast_time_windows(forecast_rows)
        for (forecast_date, time_window), values in sorted(forecast_by_day_window.items()):
            temperature_average = self._average_decimal(
                [Decimal(value) for value in values["temperatures"]]
            )
            temperature_band = (
                self._temperature_band(temperature_average)
                if temperature_average is not None
                else "ismeretlen"
            )
            condition_band = self._dominant_label(
                values["condition_counts"],
                fallback="ismeretlen",
            )

            exact_key = (time_window, temperature_band, condition_band)
            weekday_key = (time_window, forecast_date.weekday())
            if exact_key in exact_baselines:
                baseline = exact_baselines[exact_key]
                confidence = "magas"
            elif weekday_key in weekday_baselines:
                baseline = weekday_baselines[weekday_key]
                confidence = "kozepes"
            elif time_window in window_baselines:
                baseline = window_baselines[time_window]
                confidence = "alacsony"
            else:
                continue

            window_average = window_baselines.get(time_window, baseline)
            expected_revenue = Decimal(baseline["revenue"])
            historical_average = Decimal(window_average["revenue"])
            uplift_percent = (
                (expected_revenue - historical_average)
                / historical_average
                * Decimal("100")
                if historical_average > Decimal("0")
                else Decimal("0")
            )
            demand_signal = self._forecast_demand_signal(uplift_percent)
            start_hour, end_hour = self._time_window_hours(str(time_window))

            rows_by_date[forecast_date].append(
                DashboardForecastPeakTimeRow(
                    forecast_date=forecast_date,
                    time_window=str(time_window),
                    start_hour=start_hour,
                    end_hour=end_hour,
                    dominant_temperature_band=temperature_band,
                    dominant_condition_band=condition_band,
                    expected_revenue=expected_revenue,
                    expected_quantity=Decimal(baseline["quantity"]),
                    expected_transaction_count=int(
                        Decimal(baseline["transaction_count"]).to_integral_value()
                    ),
                    historical_average_revenue=historical_average,
                    revenue_uplift_percent=uplift_percent,
                    confidence=confidence,
                    demand_signal=demand_signal,
                    recommendation=self._peak_time_forecast_recommendation(
                        time_window=str(time_window),
                        demand_signal=demand_signal,
                    ),
                    source_layer="weather_forecast_peak_time_model",
                )
            )

        peak_rows: list[DashboardForecastPeakTimeRow] = []
        for forecast_date in sorted(rows_by_date):
            ranked = sorted(
                rows_by_date[forecast_date],
                key=lambda row: (row.expected_revenue, row.expected_transaction_count),
                reverse=True,
            )
            peak_rows.extend(ranked[:2])

        return peak_rows[:14]

    def _build_historical_weather_time_windows(
        self,
        *,
        rows: list[ImportRowModel],
    ) -> list[dict[str, object]]:
        occurred_values = [
            occurred_at
            for row in rows
            if (occurred_at := self._payload_occurred_at(row.normalized_payload or {}))
            is not None
        ]
        if not occurred_values:
            return []

        observations = self._list_shared_weather_observations(
            start_at=min(occurred_values),
            end_at=max(occurred_values) + timedelta(hours=1),
        )
        if not observations:
            return []

        weather_by_hour = {
            self._hour_start_utc(observation.observed_at): observation
            for observation in observations
        }
        windows: dict[tuple[date, str], dict[str, Any]] = defaultdict(
            lambda: {
                "revenue": Decimal("0"),
                "quantity": Decimal("0"),
                "receipt_keys": set(),
                "temperatures": [],
                "condition_counts": defaultdict(int),
            }
        )

        for row in rows:
            payload = row.normalized_payload or {}
            occurred_at = self._payload_occurred_at(payload)
            if occurred_at is None:
                continue

            observation = weather_by_hour.get(self._hour_start_utc(occurred_at))
            if observation is None:
                continue

            local_value = occurred_at.astimezone(APP_TIME_ZONE)
            time_window = self._time_window_label(local_value.hour)
            key = (local_value.date(), time_window)
            windows[key]["revenue"] += self._parse_decimal(payload.get("gross_amount"))
            windows[key]["quantity"] += self._parse_decimal(payload.get("quantity"))
            windows[key]["receipt_keys"].add(
                self._extract_optional_text(payload.get("receipt_no")) or str(row.id)
            )
            if observation.temperature_c is not None:
                windows[key]["temperatures"].append(Decimal(observation.temperature_c))
            windows[key]["condition_counts"][
                self._weather_condition_band(observation)
            ] += 1

        historical_windows: list[dict[str, object]] = []
        for (local_date, time_window), values in windows.items():
            average_temperature = self._average_decimal(values["temperatures"])
            historical_windows.append(
                {
                    "date": local_date,
                    "weekday": local_date.weekday(),
                    "time_window": time_window,
                    "revenue": Decimal(values["revenue"]),
                    "quantity": Decimal(values["quantity"]),
                    "transaction_count": Decimal(len(values["receipt_keys"])),
                    "temperature_band": (
                        self._temperature_band(average_temperature)
                        if average_temperature is not None
                        else "ismeretlen"
                    ),
                    "condition_band": self._dominant_label(
                        values["condition_counts"],
                        fallback="ismeretlen",
                    ),
                }
            )

        return historical_windows

    def _aggregate_forecast_days(
        self,
        forecasts: list[WeatherForecastHourlyModel],
    ) -> dict[date, dict[str, Any]]:
        forecast_days: dict[date, dict[str, Any]] = defaultdict(
            lambda: {
                "hour_count": 0,
                "temperatures": [],
                "precipitation_sum": Decimal("0"),
                "condition_counts": defaultdict(int),
                "latest_forecast_run_at": None,
            }
        )
        for forecast in forecasts:
            local_date = forecast.forecasted_at.astimezone(APP_TIME_ZONE).date()
            forecast_days[local_date]["hour_count"] += 1
            if forecast.temperature_c is not None:
                forecast_days[local_date]["temperatures"].append(
                    Decimal(forecast.temperature_c)
                )
            forecast_days[local_date]["precipitation_sum"] += (
                self._forecast_precipitation(forecast)
            )
            forecast_days[local_date]["condition_counts"][
                self._forecast_condition_band(forecast)
            ] += 1
            latest = forecast_days[local_date]["latest_forecast_run_at"]
            if latest is None or (
                forecast.forecast_run_at is not None
                and forecast.forecast_run_at > latest
            ):
                forecast_days[local_date][
                    "latest_forecast_run_at"
                ] = forecast.forecast_run_at

        return forecast_days

    @staticmethod
    def _average_revenue_by_key(
        days: list[dict[str, object]],
        *,
        key_builder: Any,
    ) -> dict[Any, Decimal]:
        grouped: dict[Any, list[Decimal]] = defaultdict(list)
        for day in days:
            grouped[key_builder(day)].append(Decimal(day["revenue"]))
        return {
            key: SqlAlchemyAnalyticsRepository._average_decimal(values) or Decimal("0")
            for key, values in grouped.items()
        }

    @staticmethod
    def _average_category_sales_by_key(
        days: list[dict[str, object]],
        *,
        key_builder: Any,
    ) -> dict[Any, dict[str, Decimal]]:
        grouped: dict[Any, dict[str, list[Decimal]]] = defaultdict(
            lambda: {"revenue": [], "quantity": []}
        )
        for day in days:
            key = key_builder(day)
            grouped[key]["revenue"].append(Decimal(day["revenue"]))
            grouped[key]["quantity"].append(Decimal(day["quantity"]))

        return {
            key: {
                "revenue": SqlAlchemyAnalyticsRepository._average_decimal(
                    values["revenue"]
                )
                or Decimal("0"),
                "quantity": SqlAlchemyAnalyticsRepository._average_decimal(
                    values["quantity"]
                )
                or Decimal("0"),
            }
            for key, values in grouped.items()
        }

    @staticmethod
    def _average_product_sales_by_key(
        days: list[dict[str, object]],
        *,
        key_builder: Any,
    ) -> dict[Any, dict[str, Decimal]]:
        return SqlAlchemyAnalyticsRepository._average_category_sales_by_key(
            days,
            key_builder=key_builder,
        )

    @staticmethod
    def _average_window_sales_by_key(
        rows: list[dict[str, object]],
        *,
        key_builder: Any,
    ) -> dict[Any, dict[str, Decimal]]:
        grouped: dict[Any, dict[str, list[Decimal]]] = defaultdict(
            lambda: {"revenue": [], "quantity": [], "transaction_count": []}
        )
        for row in rows:
            key = key_builder(row)
            grouped[key]["revenue"].append(Decimal(row["revenue"]))
            grouped[key]["quantity"].append(Decimal(row["quantity"]))
            grouped[key]["transaction_count"].append(Decimal(row["transaction_count"]))

        return {
            key: {
                "revenue": SqlAlchemyAnalyticsRepository._average_decimal(
                    values["revenue"]
                )
                or Decimal("0"),
                "quantity": SqlAlchemyAnalyticsRepository._average_decimal(
                    values["quantity"]
                )
                or Decimal("0"),
                "transaction_count": SqlAlchemyAnalyticsRepository._average_decimal(
                    values["transaction_count"]
                )
                or Decimal("0"),
            }
            for key, values in grouped.items()
        }

    @staticmethod
    def _dominant_product_categories(
        days: list[dict[str, object]],
    ) -> dict[str, str]:
        category_counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
        for day in days:
            product_name = str(day["product_name"])
            category_name = str(day["category_name"])
            category_counts[product_name][category_name] += 1
        return {
            product_name: SqlAlchemyAnalyticsRepository._dominant_label(
                counts,
                fallback=UNKNOWN_CATEGORY,
            )
            for product_name, counts in category_counts.items()
        }

    def _aggregate_forecast_time_windows(
        self,
        forecasts: list[WeatherForecastHourlyModel],
    ) -> dict[tuple[date, str], dict[str, Any]]:
        windows: dict[tuple[date, str], dict[str, Any]] = defaultdict(
            lambda: {"temperatures": [], "condition_counts": defaultdict(int)}
        )
        for forecast in forecasts:
            local_value = forecast.forecasted_at.astimezone(APP_TIME_ZONE)
            time_window = self._time_window_label(local_value.hour)
            key = (local_value.date(), time_window)
            if forecast.temperature_c is not None:
                windows[key]["temperatures"].append(Decimal(forecast.temperature_c))
            windows[key]["condition_counts"][
                self._forecast_condition_band(forecast)
            ] += 1
        return windows

    @staticmethod
    def _time_window_label(hour: int) -> str:
        if 6 <= hour < 10:
            return "Reggel"
        if 10 <= hour < 13:
            return "Délelőtt"
        if 13 <= hour < 17:
            return "Délután"
        if 17 <= hour < 22:
            return "Este"
        return "Zárás körül"

    @staticmethod
    def _time_window_hours(time_window: str) -> tuple[int, int]:
        windows = {
            "Reggel": (6, 10),
            "Délelőtt": (10, 13),
            "Délután": (13, 17),
            "Este": (17, 22),
            "Zárás körül": (22, 6),
        }
        return windows.get(time_window, (0, 24))

    @staticmethod
    def _average_decimal(values: list[Decimal]) -> Decimal | None:
        if not values:
            return None
        return sum(values, Decimal("0")) / Decimal(len(values))

    @staticmethod
    def _forecast_demand_signal(uplift_percent: Decimal) -> str:
        if uplift_percent >= Decimal("20"):
            return "emelkedo"
        if uplift_percent <= Decimal("-15"):
            return "visszafogott"
        return "normal"

    @staticmethod
    def _dominant_label(counts: dict[str, int], *, fallback: str) -> str:
        if not counts:
            return fallback
        return max(counts.items(), key=lambda item: item[1])[0]

    @staticmethod
    def _forecast_precipitation(forecast: WeatherForecastHourlyModel) -> Decimal:
        values = (
            forecast.precipitation_mm,
            forecast.rain_mm,
            forecast.snowfall_cm,
        )
        return max((Decimal(value or 0) for value in values), default=Decimal("0"))

    @classmethod
    def _forecast_condition_band(cls, forecast: WeatherForecastHourlyModel) -> str:
        if cls._forecast_precipitation(forecast) > Decimal("0"):
            return "csapadekos"
        cloud_cover = Decimal(forecast.cloud_cover_percent or 0)
        if cloud_cover >= Decimal("70"):
            return "borult"
        if cloud_cover >= Decimal("35"):
            return "reszben_felhos"
        return "napos_szaraz"

    @staticmethod
    def _forecast_recommendation(
        *,
        scope: str,
        temperature_band: str,
        condition_band: str,
        expected_revenue: Decimal,
        historical_average: Decimal,
    ) -> str:
        revenue_is_above_average = (
            historical_average > Decimal("0")
            and expected_revenue >= historical_average * Decimal("1.10")
        )
        if scope == "flow":
            if condition_band == "csapadekos":
                return "Esos event-nap lehet: beleptetes, ruhatar es fedett sorbanallas kapjon figyelmet."
            if revenue_is_above_average:
                return "A forecast eros napot jelez: pult es szemelyzet kapacitasat erdemes elore emelni."
            return "Event es pult tervhez hasznalhato idojaras-kontekstus, kezi ellenorzessel."

        if temperature_band == "kanikula":
            return "Kanikula varhato: fagyi, hideg ital es gyors pultkapacitas legyen eloterben."
        if condition_band == "csapadekos":
            return "Csapadek varhato: fedett fogyasztas, sutik es meleg italok kaphatnak nagyobb szerepet."
        if revenue_is_above_average:
            return "A hasonlo idojaras historikusan erosebb napot hozott: keszlet es termeles emelese javasolt."
        return "Normal keszultseg, de a forecast frissulese utan a becsles automatikusan valtozhat."

    @staticmethod
    def _category_forecast_recommendation(
        *,
        category_name: str,
        temperature_band: str,
        condition_band: str,
        demand_signal: str,
    ) -> str:
        normalized_category = category_name.casefold()
        if "fagyi" in normalized_category or "fagylalt" in normalized_category:
            if temperature_band in {"meleg", "kanikula"}:
                return "Meleg forecast mellett fagyi fronton elore keszultseg, feltoltott pult es gyors kiszolgalas javasolt."
            if condition_band == "csapadekos":
                return "Csapadeknal a fagyi kereslet ovatosabban kezelendo, a frissitesi ritmus legyen kontrollalt."
        if "kave" in normalized_category or "kávé" in normalized_category:
            return "Kave kategoriaban idojarastol fuggetlen stabil jelenlet varhato, reggeli es delutani idosav figyelendo."
        if "sos" in normalized_category or "sós" in normalized_category:
            return "Sos kategoriaban erdemes a gyorsan fogyaszthato pultkeszletet es a sutemritmust elore igazítani."
        if "edes" in normalized_category or "édes" in normalized_category:
            return "Edes kategoriaban a kirakati frissesseg es a darabos keszlet adhatja a legtobb uzleti hatast."
        if demand_signal == "emelkedo":
            return "A forecast a kategoriaban atlag feletti keresletet jelez, keszlet es pultkapacitas emelese javasolt."
        if demand_signal == "visszafogott":
            return "A forecast ovatosabb keresletet jelez, termelesi mennyiseget erdemes kontrollalni."
        return "Normal kategoriakeszultseg javasolt, a kovetkezo forecast frissites utan a becsles valtozhat."

    @staticmethod
    def _product_forecast_recommendation(
        *,
        product_name: str,
        demand_signal: str,
        condition_band: str,
    ) -> str:
        if demand_signal == "emelkedo":
            return (
                f"{product_name}: a forecast a termeknel atlag feletti keresletet jelez. "
                "Pultfeltoltes, recept-alapanyag es gyors kiszolgalasi keszultseg javasolt."
            )
        if demand_signal == "visszafogott":
            return (
                f"{product_name}: a forecast visszafogottabb keresletet jelez, "
                "a friss keszletet erdemes kontrollaltan tartani."
            )
        if condition_band == "csapadekos":
            return (
                f"{product_name}: csapadekos idosavban a fedett fogyasztasi es elviteles "
                "ritmus alapjan erdemes figyelni."
            )
        return (
            f"{product_name}: normal termekkeszultseg javasolt, a kovetkezo forecast "
            "frissites utan a becsles valtozhat."
        )

    @staticmethod
    def _peak_time_forecast_recommendation(
        *,
        time_window: str,
        demand_signal: str,
    ) -> str:
        if demand_signal == "emelkedo":
            return (
                f"{time_window}: a forecast erosabb forgalmi idosavot jelez. "
                "Szemelyzet, pultfeltoltes es gyors kiszolgalasi ritmus elokeszitese javasolt."
            )
        if demand_signal == "visszafogott":
            return (
                f"{time_window}: visszafogottabb idosav varhato, a termelesi es pultfeltoltesi "
                "ritmust erdemes ovatosan tartani."
            )
        return (
            f"{time_window}: normal csucsidos elokeszites javasolt, a forecast cache frissulese "
            "utan a jelzes automatikusan pontosodik."
        )

    def _build_forecast_preparation_insights(
        self,
        *,
        business_unit_id: uuid.UUID | None,
        scope: str,
        demand_rows: list[DashboardForecastCategoryDemandRow],
        limit: int,
    ) -> list[DashboardForecastPreparationRow]:
        if scope == "flow" or not demand_rows:
            return []

        products_by_category = self._build_active_products_by_category(
            business_unit_id=business_unit_id
        )
        recipe_ingredients = self._build_active_recipe_ingredients(
            business_unit_id=business_unit_id
        )
        stock_levels = self._build_inventory_stock_level_summary(
            business_unit_id=business_unit_id
        )

        preparation_rows: list[DashboardForecastPreparationRow] = []
        for demand_row in demand_rows:
            products = products_by_category.get(demand_row.category_name.casefold(), [])
            product_count = len(products)
            if product_count == 0:
                preparation_rows.append(
                    DashboardForecastPreparationRow(
                        forecast_date=demand_row.forecast_date,
                        category_name=demand_row.category_name,
                        expected_revenue=demand_row.expected_revenue,
                        expected_quantity=demand_row.expected_quantity,
                        demand_signal=demand_row.demand_signal,
                        confidence=demand_row.confidence,
                        product_count=0,
                        risky_product_count=0,
                        low_stock_ingredient_count=0,
                        missing_stock_ingredient_count=0,
                        readiness_level="figyelendo",
                        recommendation=(
                            "Van kategória-előrejelzés, de nincs stabil katalógus "
                            "kapcsolat ehhez a kategóriához. A termékeket érdemes "
                            "összekötni a recept és készlet adatokkal."
                        ),
                        source_layer="weather_forecast_catalog_inventory_model",
                    )
                )
                continue

            expected_per_product = demand_row.expected_quantity / Decimal(product_count)
            risky_product_count = 0
            low_stock_count = 0
            missing_stock_count = 0

            for product in products:
                ingredients = recipe_ingredients.get(product.id, [])
                product_has_risk = False
                if not ingredients and product.default_unit_cost is None:
                    risky_product_count += 1
                    continue

                for ingredient in ingredients:
                    stock_level = stock_levels.get(ingredient.inventory_item_id)
                    if stock_level is None or int(stock_level["movement_count"]) == 0:
                        missing_stock_count += 1
                        product_has_risk = True
                        continue

                    current_quantity = Decimal(stock_level["current_quantity"])
                    required_quantity = Decimal(ingredient.quantity) * max(
                        expected_per_product,
                        Decimal("1"),
                    )
                    if current_quantity <= Decimal("0"):
                        missing_stock_count += 1
                        product_has_risk = True
                    elif current_quantity < required_quantity:
                        low_stock_count += 1
                        product_has_risk = True

                if product_has_risk:
                    risky_product_count += 1

            readiness_level = self._forecast_preparation_readiness(
                demand_signal=demand_row.demand_signal,
                confidence=demand_row.confidence,
                product_count=product_count,
                risky_product_count=risky_product_count,
                low_stock_count=low_stock_count,
                missing_stock_count=missing_stock_count,
            )
            preparation_rows.append(
                DashboardForecastPreparationRow(
                    forecast_date=demand_row.forecast_date,
                    category_name=demand_row.category_name,
                    expected_revenue=demand_row.expected_revenue,
                    expected_quantity=demand_row.expected_quantity,
                    demand_signal=demand_row.demand_signal,
                    confidence=demand_row.confidence,
                    product_count=product_count,
                    risky_product_count=risky_product_count,
                    low_stock_ingredient_count=low_stock_count,
                    missing_stock_ingredient_count=missing_stock_count,
                    readiness_level=readiness_level,
                    recommendation=self._forecast_preparation_recommendation(
                        category_name=demand_row.category_name,
                        demand_signal=demand_row.demand_signal,
                        readiness_level=readiness_level,
                        risky_product_count=risky_product_count,
                        low_stock_count=low_stock_count,
                        missing_stock_count=missing_stock_count,
                    ),
                    source_layer="weather_forecast_catalog_inventory_model",
                )
            )

        return sorted(
            preparation_rows,
            key=lambda row: (
                row.forecast_date,
                -self._preparation_readiness_rank(row.readiness_level),
                -row.expected_revenue,
            ),
        )[:limit]

    def _build_active_products_by_category(
        self,
        *,
        business_unit_id: uuid.UUID | None,
    ) -> dict[str, list[ProductModel]]:
        statement = (
            select(ProductModel, CategoryModel.name)
            .outerjoin(CategoryModel, ProductModel.category_id == CategoryModel.id)
            .where(ProductModel.is_active.is_(True))
            .order_by(ProductModel.name.asc())
        )
        if business_unit_id is not None:
            statement = statement.where(ProductModel.business_unit_id == business_unit_id)

        products_by_category: dict[str, list[ProductModel]] = defaultdict(list)
        for product, category_name in self._session.execute(statement).all():
            if not category_name:
                continue
            products_by_category[str(category_name).casefold()].append(product)
        return dict(products_by_category)

    @staticmethod
    def _forecast_preparation_readiness(
        *,
        demand_signal: str,
        confidence: str,
        product_count: int,
        risky_product_count: int,
        low_stock_count: int,
        missing_stock_count: int,
    ) -> str:
        if missing_stock_count > 0 or (
            product_count > 0
            and risky_product_count >= product_count
            and low_stock_count == 0
        ):
            return "kritikus"
        if low_stock_count > 0 or demand_signal == "emelkedo" or confidence == "alacsony":
            return "figyelendo"
        return "rendben"

    @staticmethod
    def _preparation_readiness_rank(readiness_level: str) -> int:
        ranks = {"kritikus": 3, "figyelendo": 2, "rendben": 1}
        return ranks.get(readiness_level, 0)

    @staticmethod
    def _forecast_preparation_recommendation(
        *,
        category_name: str,
        demand_signal: str,
        readiness_level: str,
        risky_product_count: int,
        low_stock_count: int,
        missing_stock_count: int,
    ) -> str:
        if missing_stock_count > 0:
            return (
                f"{category_name}: előrejelzett kereslet mellett {missing_stock_count} "
                "alapanyaghoz hiányzik vagy nulla a készlet. Beszerzés vagy készletkorrekció "
                "javasolt a termelés előtt."
            )
        if low_stock_count > 0:
            return (
                f"{category_name}: a becsült mennyiséghez {low_stock_count} alapanyag "
                "alacsony készleten áll. Termelés előtt pult- és raktárkészlet ellenőrzés javasolt."
            )
        if risky_product_count > 0:
            return (
                f"{category_name}: {risky_product_count} terméknél hiányos a recept vagy "
                "költségalap, ezért a javaslat üzletileg óvatosan kezelendő."
            )
        if demand_signal == "emelkedo":
            return (
                f"{category_name}: az előrejelzés átlag feletti keresletet jelez. "
                "Érdemes korábban indítani az előkészítést és a gyorsan fogyó termékeket feltölteni."
            )
        if readiness_level == "rendben":
            return (
                f"{category_name}: a forecast és a jelenlegi katalógus-készlet kapcsolat alapján "
                "nincs kiemelt előkészítési kockázat."
            )
        return (
            f"{category_name}: normál előkészítés javasolt, a következő forecast frissítés "
            "után az ajánlás automatikusan változhat."
        )

    def _build_flow_forecast_event_insights(
        self,
        *,
        business_unit_id: uuid.UUID | None,
        scope: str,
        limit: int,
    ) -> list[DashboardFlowForecastEventRow]:
        if scope != "flow" or business_unit_id is None:
            return []

        now = datetime.now(APP_TIME_ZONE)
        forecast_end = now + timedelta(days=FORECAST_IMPACT_DAYS)
        events = self._list_upcoming_flow_events(
            business_unit_id=business_unit_id,
            starts_from=now,
            starts_to=forecast_end,
            limit=limit,
        )
        if not events:
            return []

        forecast_rows = self._list_shared_weather_forecasts(
            start_at=now,
            end_at=forecast_end + timedelta(hours=8),
        )
        forecasts_by_hour = {
            self._hour_start_utc(forecast.forecasted_at): forecast
            for forecast in forecast_rows
        }

        insights: list[DashboardFlowForecastEventRow] = []
        for event in events:
            starts_at = self._as_app_time(event.starts_at)
            ends_at = (
                self._as_app_time(event.ends_at)
                if event.ends_at is not None
                else starts_at + timedelta(hours=8)
            )
            event_forecasts = self._event_forecast_window(
                forecasts_by_hour=forecasts_by_hour,
                starts_at=starts_at,
                ends_at=ends_at,
            )
            insights.append(
                self._build_flow_event_forecast_row(
                    event=event,
                    starts_at=starts_at,
                    ends_at=ends_at,
                    forecasts=event_forecasts,
                )
            )

        return insights

    def _list_upcoming_flow_events(
        self,
        *,
        business_unit_id: uuid.UUID,
        starts_from: datetime,
        starts_to: datetime,
        limit: int,
    ) -> list[EventModel]:
        statement = (
            select(EventModel)
            .where(EventModel.business_unit_id == business_unit_id)
            .where(EventModel.is_active.is_(True))
            .where(EventModel.status.in_(("planned", "confirmed")))
            .where(EventModel.starts_at >= starts_from)
            .where(EventModel.starts_at <= starts_to)
            .order_by(EventModel.starts_at.asc())
            .limit(limit)
        )
        return list(self._session.scalars(statement).all())

    def _event_forecast_window(
        self,
        *,
        forecasts_by_hour: dict[datetime, WeatherForecastHourlyModel],
        starts_at: datetime,
        ends_at: datetime,
    ) -> list[WeatherForecastHourlyModel]:
        current = self._hour_start_utc(starts_at)
        end_hour = self._hour_start_utc(ends_at)
        forecasts: list[WeatherForecastHourlyModel] = []
        while current <= end_hour:
            forecast = forecasts_by_hour.get(current)
            if forecast is not None:
                forecasts.append(forecast)
            current += timedelta(hours=1)
        return forecasts

    def _build_flow_event_forecast_row(
        self,
        *,
        event: EventModel,
        starts_at: datetime,
        ends_at: datetime,
        forecasts: list[WeatherForecastHourlyModel],
    ) -> DashboardFlowForecastEventRow:
        if not forecasts:
            return DashboardFlowForecastEventRow(
                event_id=event.id,
                title=event.title,
                performer_name=event.performer_name,
                starts_at=starts_at,
                ends_at=ends_at,
                expected_attendance=event.expected_attendance,
                forecast_hours=0,
                dominant_condition_band="ismeretlen",
                average_temperature_c=None,
                precipitation_mm=Decimal("0"),
                average_wind_speed_kmh=None,
                preparation_level="figyelendo",
                focus_area="Forecast lefedettség",
                recommendation=(
                    "Ehhez az event-idősávhoz még nincs forecast cache. A háttér szinkron "
                    "következő futása után az előkészítési jelzés automatikusan pontosodik."
                ),
                source_layer="weather_forecast_event_model",
            )

        condition_counts: dict[str, int] = defaultdict(int)
        temperatures: list[Decimal] = []
        wind_speeds: list[Decimal] = []
        precipitation = Decimal("0")
        for forecast in forecasts:
            condition_counts[self._forecast_condition_band(forecast)] += 1
            if forecast.temperature_c is not None:
                temperatures.append(Decimal(forecast.temperature_c))
            if forecast.wind_speed_kmh is not None:
                wind_speeds.append(Decimal(forecast.wind_speed_kmh))
            precipitation += self._forecast_precipitation(forecast)

        average_temperature = self._average_decimal(temperatures)
        average_wind = self._average_decimal(wind_speeds)
        condition_band = self._dominant_label(
            condition_counts,
            fallback="ismeretlen",
        )
        focus_area = self._flow_event_forecast_focus_area(
            condition_band=condition_band,
            average_temperature=average_temperature,
            precipitation=precipitation,
            average_wind=average_wind,
            expected_attendance=event.expected_attendance,
        )
        preparation_level = self._flow_event_preparation_level(
            condition_band=condition_band,
            precipitation=precipitation,
            average_wind=average_wind,
            expected_attendance=event.expected_attendance,
        )

        return DashboardFlowForecastEventRow(
            event_id=event.id,
            title=event.title,
            performer_name=event.performer_name,
            starts_at=starts_at,
            ends_at=ends_at,
            expected_attendance=event.expected_attendance,
            forecast_hours=len(forecasts),
            dominant_condition_band=condition_band,
            average_temperature_c=average_temperature,
            precipitation_mm=precipitation,
            average_wind_speed_kmh=average_wind,
            preparation_level=preparation_level,
            focus_area=focus_area,
            recommendation=self._flow_event_forecast_recommendation(
                title=event.title,
                condition_band=condition_band,
                average_temperature=average_temperature,
                precipitation=precipitation,
                average_wind=average_wind,
                expected_attendance=event.expected_attendance,
                preparation_level=preparation_level,
            ),
            source_layer="weather_forecast_event_model",
        )

    @staticmethod
    def _flow_event_preparation_level(
        *,
        condition_band: str,
        precipitation: Decimal,
        average_wind: Decimal | None,
        expected_attendance: int | None,
    ) -> str:
        attendance = expected_attendance or 0
        wind = average_wind or Decimal("0")
        if precipitation >= Decimal("2") or (
            condition_band == "csapadekos" and attendance >= 200
        ):
            return "kritikus"
        if wind >= Decimal("28") or attendance >= 300:
            return "kritikus"
        if condition_band in {"csapadekos", "borult"}:
            return "figyelendo"
        if wind >= Decimal("20") or attendance >= 180:
            return "figyelendo"
        return "rendben"

    @staticmethod
    def _flow_event_forecast_focus_area(
        *,
        condition_band: str,
        average_temperature: Decimal | None,
        precipitation: Decimal,
        average_wind: Decimal | None,
        expected_attendance: int | None,
    ) -> str:
        attendance = expected_attendance or 0
        wind = average_wind or Decimal("0")
        if condition_band == "csapadekos" or precipitation > Decimal("0"):
            return "Beléptetés, ruhatár és fedett sor"
        if wind >= Decimal("20"):
            return "Kültéri sor és biztonság"
        if average_temperature is not None and average_temperature <= Decimal("8"):
            return "Ruhatár és érkezési ritmus"
        if average_temperature is not None and average_temperature >= Decimal("27"):
            return "Hűtött ital és bárpult"
        if attendance >= 180:
            return "Személyzet és pultkapacitás"
        return "Normál event előkészítés"

    @staticmethod
    def _flow_event_forecast_recommendation(
        *,
        title: str,
        condition_band: str,
        average_temperature: Decimal | None,
        precipitation: Decimal,
        average_wind: Decimal | None,
        expected_attendance: int | None,
        preparation_level: str,
    ) -> str:
        attendance = expected_attendance or 0
        wind = average_wind or Decimal("0")
        if condition_band == "csapadekos" or precipitation > Decimal("0"):
            return (
                f"{title}: csapadékos forecast látszik az event idősávában. "
                "Beléptetésnél fedett sor, ruhatár és gyors pultnyitás legyen előkészítve."
            )
        if wind >= Decimal("20"):
            return (
                f"{title}: szelesebb idő várható. Kültéri sor, beengedési pontok és "
                "biztonsági útvonalak előzetes ellenőrzése javasolt."
            )
        if average_temperature is not None and average_temperature <= Decimal("8"):
            return (
                f"{title}: hűvös event-idősáv várható. Ruhatár, meleg ital és érkezési "
                "csúcsidő kezelése legyen fókuszban."
            )
        if average_temperature is not None and average_temperature >= Decimal("27"):
            return (
                f"{title}: meleg forecast mellett hideg ital, víz és gyors bárpult "
                "kapacitás adhat üzleti előnyt."
            )
        if attendance >= 180:
            return (
                f"{title}: a várható létszám alapján pult- és személyzeti kapacitást "
                "érdemes előre ellenőrizni."
            )
        if preparation_level == "rendben":
            return (
                f"{title}: a forecast alapján nincs kiemelt időjárási előkészítési kockázat, "
                "normál event terv elegendő."
            )
        return (
            f"{title}: az event forecast jelzése figyelendő, a következő cache frissítés "
            "után az ajánlás automatikusan pontosodik."
        )

    def _list_shared_weather_forecasts(
        self,
        *,
        start_at: datetime,
        end_at: datetime,
    ) -> list[WeatherForecastHourlyModel]:
        period_start = self._hour_start_utc(start_at)
        period_end = self._hour_start_utc(end_at)
        statement = (
            select(WeatherForecastHourlyModel)
            .join(
                WeatherLocationModel,
                WeatherForecastHourlyModel.weather_location_id
                == WeatherLocationModel.id,
            )
            .where(WeatherLocationModel.scope == "shared")
            .where(WeatherLocationModel.name == SHARED_WEATHER_LOCATION_NAME)
            .where(WeatherLocationModel.provider == SHARED_WEATHER_PROVIDER)
            .where(WeatherForecastHourlyModel.provider == SHARED_WEATHER_PROVIDER)
            .where(WeatherForecastHourlyModel.forecasted_at >= period_start)
            .where(WeatherForecastHourlyModel.forecasted_at <= period_end)
            .order_by(WeatherForecastHourlyModel.forecasted_at.asc())
        )
        return list(self._session.scalars(statement).all())

    @staticmethod
    def _temperature_band(value: Decimal) -> str:
        if value < Decimal("10"):
            return "hideg"
        if value < Decimal("20"):
            return "enyhe"
        if value < Decimal("28"):
            return "meleg"
        return "kanikula"

    @classmethod
    def _weather_condition_band(cls, observation: WeatherObservationHourlyModel) -> str:
        if cls._observation_precipitation(observation) > Decimal("0"):
            return "csapadekos"
        cloud_cover = Decimal(observation.cloud_cover_percent or 0)
        if cloud_cover >= Decimal("70"):
            return "borult"
        if cloud_cover >= Decimal("35"):
            return "reszben_felhos"
        return "napos_szaraz"

    @staticmethod
    def _observation_precipitation(observation: WeatherObservationHourlyModel) -> Decimal:
        values = (
            observation.precipitation_mm,
            observation.rain_mm,
            observation.snowfall_cm,
        )
        return max((Decimal(value or 0) for value in values), default=Decimal("0"))

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

    def _build_basket_pairs(
        self,
        *,
        rows: list[ImportRowModel],
        start_at: datetime,
        end_at: datetime,
        limit: int,
    ) -> list[DashboardBasketPairRow]:
        baskets: dict[str, dict[str, Decimal]] = defaultdict(lambda: defaultdict(Decimal))

        for row in rows:
            payload = row.normalized_payload or {}
            occurred_at = self._payload_occurred_at(payload)
            if occurred_at is None or occurred_at < start_at or occurred_at > end_at:
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
        start_at: datetime,
        end_at: datetime,
        product_a: str,
        product_b: str,
        limit: int,
    ) -> list[DashboardBasketReceipt]:
        basket_rows: dict[str, list[ImportRowModel]] = defaultdict(list)

        for row in rows:
            payload = row.normalized_payload or {}
            occurred_at = self._payload_occurred_at(payload)
            if occurred_at is None or occurred_at < start_at or occurred_at > end_at:
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

    def _build_supplier_invoice_tax_totals(
        self,
        invoice_ids: list[uuid.UUID],
    ) -> dict[uuid.UUID, dict[str, Decimal]]:
        if not invoice_ids:
            return {}

        rows = self._session.execute(
            select(
                PurchaseInvoiceLineModel.invoice_id,
                sa.func.coalesce(sa.func.sum(PurchaseInvoiceLineModel.line_net_amount), 0),
                sa.func.coalesce(sa.func.sum(PurchaseInvoiceLineModel.vat_amount), 0),
            )
            .where(PurchaseInvoiceLineModel.invoice_id.in_(invoice_ids))
            .group_by(PurchaseInvoiceLineModel.invoice_id)
        ).all()
        return {
            invoice_id: {
                "net_amount": Decimal(net_amount),
                "vat_amount": Decimal(vat_amount),
            }
            for invoice_id, net_amount, vat_amount in rows
        }

    def _build_expense_breakdown(
        self,
        *,
        transactions: list[FinancialTransactionModel],
        limit: int,
    ) -> list[DashboardExpenseRow]:
        tax_totals = self._build_supplier_invoice_tax_totals(
            [
                transaction.source_id
                for transaction in transactions
                if transaction.direction == "outflow"
                and transaction.source_type == SUPPLIER_INVOICE_SOURCE_TYPE
            ]
        )
        aggregate: dict[str, dict[str, Decimal | int]] = defaultdict(
            lambda: {
                "amount": Decimal("0"),
                "net_amount": Decimal("0"),
                "vat_amount": Decimal("0"),
                "tax_count": 0,
                "count": 0,
            }
        )

        for transaction in transactions:
            if transaction.direction != "outflow":
                continue

            label = transaction.transaction_type or "expense"
            amount = Decimal(transaction.amount)
            aggregate[label]["amount"] += amount
            aggregate[label]["count"] += 1
            tax_total = tax_totals.get(transaction.source_id)
            if tax_total is not None:
                aggregate[label]["net_amount"] += tax_total["net_amount"]
                aggregate[label]["vat_amount"] += tax_total["vat_amount"]
                aggregate[label]["tax_count"] += 1

        sorted_rows = sorted(
            aggregate.items(),
            key=lambda item: Decimal(item[1]["amount"]),
            reverse=True,
        )
        return [
            DashboardExpenseRow(
                label=label,
                amount=Decimal(values["amount"]),
                gross_amount=Decimal(values["amount"]),
                net_amount=(
                    Decimal(values["net_amount"])
                    if int(values["tax_count"]) > 0
                    else None
                ),
                vat_amount=(
                    Decimal(values["vat_amount"])
                    if int(values["tax_count"]) > 0
                    else None
                ),
                transaction_count=int(values["count"]),
                source_layer="financial_actual",
                amount_basis="gross",
                tax_breakdown_source=(
                    "supplier_invoice_actual"
                    if int(values["tax_count"]) == int(values["count"])
                    else (
                        "partial_supplier_invoice_actual"
                        if int(values["tax_count"]) > 0
                        else "not_available"
                    )
                ),
            )
            for label, values in sorted_rows[:limit]
        ]

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
    def _hour_start_utc(value: datetime) -> datetime:
        aware_value = (
            value.replace(tzinfo=UTC)
            if value.tzinfo is None
            else value.astimezone(UTC)
        )
        return aware_value.replace(minute=0, second=0, microsecond=0)

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
