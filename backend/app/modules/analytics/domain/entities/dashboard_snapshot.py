"""Business dashboard read-model entities."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class DashboardPeriod:
    """Resolved date window used by dashboard calculations."""

    preset: str
    start_date: date
    end_date: date
    grain: str


@dataclass(frozen=True, slots=True)
class DashboardKpi:
    """One high-level business KPI tile."""

    code: str
    label: str
    value: Decimal
    unit: str
    source_layer: str
    amount_basis: str | None = None
    amount_origin: str | None = None


@dataclass(frozen=True, slots=True)
class DashboardTrendPoint:
    """Time-series point for charting revenue, cost and profit."""

    period_start: datetime
    revenue: Decimal
    cost: Decimal
    profit: Decimal
    estimated_cogs: Decimal
    margin_profit: Decimal
    revenue_amount_basis: str = "gross"
    revenue_amount_origin: str = "actual"
    cost_amount_basis: str = "gross"
    cost_amount_origin: str = "actual"


@dataclass(frozen=True, slots=True)
class DashboardBreakdownRow:
    """Aggregated row for category or product drill-down."""

    label: str
    revenue: Decimal
    net_revenue: Decimal | None
    vat_amount: Decimal | None
    quantity: Decimal
    transaction_count: int
    source_layer: str
    amount_basis: str = "gross"
    tax_breakdown_source: str = "not_available"


@dataclass(frozen=True, slots=True)
class DashboardVatReadiness:
    """Revenue VAT coverage derived from POS rows and product master data."""

    status: str
    coverage_percent: Decimal
    gross_revenue: Decimal
    covered_gross_revenue: Decimal
    missing_gross_revenue: Decimal
    total_row_count: int
    covered_row_count: int
    missing_row_count: int
    source_layer: str = "import_derived"
    amount_basis: str = "gross"
    tax_breakdown_source: str = "not_available"


@dataclass(frozen=True, slots=True)
class DashboardHeatmapCell:
    """Hourly POS traffic aggregate for one weekday and hour."""

    weekday: int
    hour: int
    revenue: Decimal
    transaction_count: int
    source_layer: str


@dataclass(frozen=True, slots=True)
class DashboardCategoryTrendRow:
    """Current vs previous period category trend row."""

    label: str
    current_revenue: Decimal
    previous_revenue: Decimal
    revenue_change: Decimal
    revenue_change_percent: Decimal
    current_quantity: Decimal
    previous_quantity: Decimal
    current_transaction_count: int
    previous_transaction_count: int
    source_layer: str


@dataclass(frozen=True, slots=True)
class DashboardWeatherCategoryInsightRow:
    """Category revenue grouped by matched hourly weather condition."""

    category_name: str
    weather_condition: str
    revenue: Decimal
    quantity: Decimal
    transaction_count: int
    average_temperature_c: Decimal | None
    source_layer: str


@dataclass(frozen=True, slots=True)
class DashboardTemperatureBandInsightRow:
    """Sales grouped by matched hourly temperature band."""

    temperature_band: str
    revenue: Decimal
    quantity: Decimal
    transaction_count: int
    basket_count: int
    average_basket_value: Decimal
    average_temperature_c: Decimal | None
    top_category_name: str
    top_category_revenue: Decimal
    source_layer: str


@dataclass(frozen=True, slots=True)
class DashboardWeatherConditionInsightRow:
    """Sales grouped by precipitation and cloudiness condition."""

    condition_band: str
    revenue: Decimal
    quantity: Decimal
    transaction_count: int
    basket_count: int
    average_basket_value: Decimal
    average_cloud_cover_percent: Decimal | None
    precipitation_mm: Decimal
    top_category_name: str
    top_category_revenue: Decimal
    source_layer: str


@dataclass(frozen=True, slots=True)
class DashboardForecastImpactRow:
    """Forecast-aware business signal for one upcoming date."""

    forecast_date: date
    forecast_hours: int
    dominant_temperature_band: str
    dominant_condition_band: str
    average_temperature_c: Decimal | None
    precipitation_mm: Decimal
    expected_revenue: Decimal
    historical_average_revenue: Decimal
    confidence: str
    recommendation: str
    forecast_updated_at: datetime | None
    source_layer: str


@dataclass(frozen=True, slots=True)
class DashboardForecastCategoryDemandRow:
    """Forecast-aware category demand signal for Gourmand planning."""

    forecast_date: date
    category_name: str
    dominant_temperature_band: str
    dominant_condition_band: str
    expected_revenue: Decimal
    expected_quantity: Decimal
    historical_average_revenue: Decimal
    revenue_uplift_percent: Decimal
    confidence: str
    demand_signal: str
    recommendation: str
    source_layer: str


@dataclass(frozen=True, slots=True)
class DashboardForecastPreparationRow:
    """Forecast-aware production and stock preparation signal for Gourmand."""

    forecast_date: date
    category_name: str
    expected_revenue: Decimal
    expected_quantity: Decimal
    demand_signal: str
    confidence: str
    product_count: int
    risky_product_count: int
    low_stock_ingredient_count: int
    missing_stock_ingredient_count: int
    readiness_level: str
    recommendation: str
    source_layer: str


@dataclass(frozen=True, slots=True)
class DashboardForecastProductDemandRow:
    """Forecast-aware product demand signal for Gourmand planning."""

    forecast_date: date
    product_name: str
    category_name: str
    dominant_temperature_band: str
    dominant_condition_band: str
    expected_revenue: Decimal
    expected_quantity: Decimal
    historical_average_revenue: Decimal
    revenue_uplift_percent: Decimal
    confidence: str
    demand_signal: str
    recommendation: str
    source_layer: str


@dataclass(frozen=True, slots=True)
class DashboardForecastPeakTimeRow:
    """Forecast-aware peak time signal for Gourmand planning."""

    forecast_date: date
    time_window: str
    start_hour: int
    end_hour: int
    dominant_temperature_band: str
    dominant_condition_band: str
    expected_revenue: Decimal
    expected_quantity: Decimal
    expected_transaction_count: int
    historical_average_revenue: Decimal
    revenue_uplift_percent: Decimal
    confidence: str
    demand_signal: str
    recommendation: str
    source_layer: str


@dataclass(frozen=True, slots=True)
class DashboardFlowForecastEventRow:
    """Forecast-aware preparation signal for upcoming Flow events."""

    event_id: uuid.UUID
    title: str
    performer_name: str | None
    starts_at: datetime
    ends_at: datetime
    expected_attendance: int | None
    forecast_hours: int
    dominant_condition_band: str
    average_temperature_c: Decimal | None
    precipitation_mm: Decimal
    average_wind_speed_kmh: Decimal | None
    preparation_level: str
    focus_area: str
    recommendation: str
    source_layer: str


@dataclass(frozen=True, slots=True)
class DashboardProductRiskRow:
    """Sellable product needing business attention."""

    product_id: uuid.UUID
    product_name: str
    category_name: str
    sale_price_gross: Decimal
    estimated_unit_cost: Decimal
    estimated_margin_amount: Decimal
    estimated_margin_percent: Decimal
    risk_level: str
    risk_reasons: tuple[str, ...]
    low_stock_ingredient_count: int
    missing_stock_ingredient_count: int
    source_layer: str


@dataclass(frozen=True, slots=True)
class DashboardStockRiskRow:
    """Inventory item needing stock attention."""

    inventory_item_id: uuid.UUID
    item_name: str
    item_type: str
    current_quantity: Decimal
    theoretical_quantity: Decimal | None
    variance_quantity: Decimal | None
    used_by_product_count: int
    movement_count: int
    last_movement_at: datetime | None
    risk_level: str
    risk_reasons: tuple[str, ...]
    source_layer: str


@dataclass(frozen=True, slots=True)
class DashboardExpenseRow:
    """Aggregated expense row for cost analysis."""

    label: str
    amount: Decimal
    gross_amount: Decimal
    net_amount: Decimal | None
    vat_amount: Decimal | None
    transaction_count: int
    source_layer: str
    amount_basis: str
    tax_breakdown_source: str


@dataclass(frozen=True, slots=True)
class DashboardProductDetailRow:
    """Product drill-down row with optional category context."""

    product_name: str
    category_name: str
    revenue: Decimal
    net_revenue: Decimal | None
    vat_amount: Decimal | None
    estimated_unit_cost_net: Decimal | None
    estimated_cogs_net: Decimal | None
    estimated_net_margin_amount: Decimal | None
    estimated_margin_percent: Decimal | None
    quantity: Decimal
    transaction_count: int
    source_layer: str
    amount_basis: str = "gross"
    tax_breakdown_source: str = "not_available"
    cost_source: str = "not_available"
    margin_status: str = "not_available"


@dataclass(frozen=True, slots=True)
class DashboardPosSourceRow:
    """POS import source row behind a product-level dashboard drill-down."""

    row_id: uuid.UUID
    row_number: int
    date: date | None
    receipt_no: str | None
    category_name: str
    product_name: str
    quantity: Decimal
    gross_amount: Decimal
    net_amount: Decimal | None
    vat_amount: Decimal | None
    vat_rate_percent: Decimal | None
    payment_method: str | None
    source_layer: str
    amount_basis: str = "gross"
    tax_breakdown_source: str = "not_available"


@dataclass(frozen=True, slots=True)
class DashboardExpenseDetailRow:
    """Expense drill-down row backed by financial transactions."""

    transaction_id: uuid.UUID
    transaction_type: str
    amount: Decimal
    gross_amount: Decimal
    net_amount: Decimal | None
    vat_amount: Decimal | None
    currency: str
    occurred_at: date
    description: str
    source_type: str
    source_id: uuid.UUID
    source_layer: str
    amount_basis: str
    tax_breakdown_source: str


@dataclass(frozen=True, slots=True)
class DashboardExpenseSourceLine:
    """Line-level source detail for an expense transaction."""

    line_id: uuid.UUID
    inventory_item_id: uuid.UUID | None
    description: str
    quantity: Decimal
    uom_id: uuid.UUID
    unit_net_amount: Decimal
    line_net_amount: Decimal
    vat_rate_id: uuid.UUID | None
    vat_amount: Decimal | None
    line_gross_amount: Decimal | None


@dataclass(frozen=True, slots=True)
class DashboardExpenseSource:
    """Source record behind one expense transaction."""

    transaction_id: uuid.UUID
    transaction_type: str
    amount: Decimal
    gross_amount: Decimal
    net_amount: Decimal | None
    vat_amount: Decimal | None
    currency: str
    occurred_at: date
    source_type: str
    source_id: uuid.UUID
    supplier_id: uuid.UUID | None
    supplier_name: str | None
    invoice_number: str | None
    invoice_date: date | None
    gross_total: Decimal | None
    net_total: Decimal | None
    vat_total: Decimal | None
    notes: str | None
    amount_basis: str
    tax_breakdown_source: str
    lines: tuple[DashboardExpenseSourceLine, ...]


@dataclass(frozen=True, slots=True)
class DashboardBasketPairRow:
    """Frequently co-purchased products derived from POS receipt groups."""

    product_a: str
    product_b: str
    basket_count: int
    total_gross_amount: Decimal
    source_layer: str


@dataclass(frozen=True, slots=True)
class DashboardBasketReceiptLine:
    """One POS row inside a source receipt basket."""

    row_id: uuid.UUID
    row_number: int
    product_name: str
    category_name: str
    quantity: Decimal
    gross_amount: Decimal
    payment_method: str | None


@dataclass(frozen=True, slots=True)
class DashboardBasketReceipt:
    """Source receipt behind one co-purchased product pair."""

    receipt_no: str
    date: date | None
    gross_amount: Decimal
    quantity: Decimal
    lines: tuple[DashboardBasketReceiptLine, ...]
    source_layer: str


@dataclass(frozen=True, slots=True)
class DashboardStatisticsTrendPoint:
    """Daily statistic point with rolling decision-support indicators."""

    business_date: date
    daily_revenue: Decimal
    basket_count: int
    average_basket_value: Decimal
    rolling_7_day_average_revenue: Decimal
    moving_7_day_median_revenue: Decimal
    rolling_7_day_average_basket_value: Decimal
    moving_7_day_median_basket_value: Decimal
    source_layer: str


@dataclass(frozen=True, slots=True)
class DashboardStatisticsOutlierFlag:
    """Explainable statistical warning derived from POS daily or basket data."""

    code: str
    severity: str
    label: str
    business_date: date | None
    metric_value: Decimal
    baseline_value: Decimal
    recommendation: str
    source_layer: str


@dataclass(frozen=True, slots=True)
class DashboardDemandPercentileRow:
    """Demand percentile preparation row for category or product demand models."""

    label: str
    scope: str
    transaction_count: int
    quantity: Decimal
    gross_revenue: Decimal
    median_daily_quantity: Decimal
    p90_daily_quantity: Decimal
    p95_daily_quantity: Decimal
    source_layer: str
    amount_basis: str = "gross"
    amount_origin: str = "actual"


@dataclass(frozen=True, slots=True)
class DashboardInventoryTurnoverReadiness:
    """Readiness signal for the next inventory-turnover read-model slice."""

    status: str
    pos_row_count: int
    product_demand_row_count: int
    category_demand_row_count: int
    required_source_layers: tuple[str, ...]
    recommendation: str
    source_layer: str


@dataclass(frozen=True, slots=True)
class DashboardStatisticsInsight:
    """Prioritized business interpretation derived from statistics signals."""

    code: str
    severity: str
    category: str
    title: str
    summary: str
    recommendation: str
    confidence: str
    priority_score: Decimal
    source_layer: str


@dataclass(frozen=True, slots=True)
class DashboardStatisticsQuality:
    """Distribution and data-quality summary for Dashboard 2.0 decisions."""

    period_day_count: int
    active_sales_day_count: int
    pos_row_count: int
    basket_count: int
    coverage_percent: Decimal
    quality_level: str
    average_daily_revenue: Decimal
    median_daily_revenue: Decimal
    p25_daily_revenue: Decimal
    p75_daily_revenue: Decimal
    p90_daily_revenue: Decimal
    p95_daily_revenue: Decimal
    average_basket_value: Decimal
    median_basket_value: Decimal
    p25_basket_value: Decimal
    p75_basket_value: Decimal
    p90_basket_value: Decimal
    p95_basket_value: Decimal
    trend_direction: str
    trend_stability: str
    trend_change_percent: Decimal
    volatility_percent: Decimal
    trend_recommendation: str
    rolling_points: tuple[DashboardStatisticsTrendPoint, ...]
    outlier_flags: tuple[DashboardStatisticsOutlierFlag, ...]
    category_demand_percentiles: tuple[DashboardDemandPercentileRow, ...]
    product_demand_percentiles: tuple[DashboardDemandPercentileRow, ...]
    inventory_turnover_readiness: DashboardInventoryTurnoverReadiness
    insights: tuple[DashboardStatisticsInsight, ...]
    recommendation: str
    source_layer: str
    amount_basis: str = "gross"
    amount_origin: str = "actual"


@dataclass(frozen=True, slots=True)
class DashboardSnapshot:
    """Top-level dashboard payload."""

    scope: str
    business_unit_id: uuid.UUID | None
    business_unit_name: str | None
    period: DashboardPeriod
    kpis: tuple[DashboardKpi, ...]
    revenue_trend: tuple[DashboardTrendPoint, ...]
    category_breakdown: tuple[DashboardBreakdownRow, ...]
    vat_readiness: DashboardVatReadiness
    payment_method_breakdown: tuple[DashboardBreakdownRow, ...]
    basket_value_distribution: tuple[DashboardBreakdownRow, ...]
    traffic_heatmap: tuple[DashboardHeatmapCell, ...]
    category_trends: tuple[DashboardCategoryTrendRow, ...]
    weather_category_insights: tuple[DashboardWeatherCategoryInsightRow, ...]
    temperature_band_insights: tuple[DashboardTemperatureBandInsightRow, ...]
    weather_condition_insights: tuple[DashboardWeatherConditionInsightRow, ...]
    forecast_impact_insights: tuple[DashboardForecastImpactRow, ...]
    forecast_category_demand_insights: tuple[DashboardForecastCategoryDemandRow, ...]
    forecast_preparation_insights: tuple[DashboardForecastPreparationRow, ...]
    forecast_product_demand_insights: tuple[DashboardForecastProductDemandRow, ...]
    forecast_peak_time_insights: tuple[DashboardForecastPeakTimeRow, ...]
    flow_forecast_event_insights: tuple[DashboardFlowForecastEventRow, ...]
    product_risks: tuple[DashboardProductRiskRow, ...]
    stock_risks: tuple[DashboardStockRiskRow, ...]
    top_products: tuple[DashboardBreakdownRow, ...]
    expense_breakdown: tuple[DashboardExpenseRow, ...]
    statistics_quality: DashboardStatisticsQuality
    notes: tuple[str, ...]
