"""Dashboard response schemas."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class DashboardPeriodResponse(BaseModel):
    """Resolved dashboard period."""

    model_config = ConfigDict(from_attributes=True)

    preset: str
    start_date: date
    end_date: date
    grain: str


class DashboardKpiResponse(BaseModel):
    """KPI tile response."""

    model_config = ConfigDict(from_attributes=True)

    code: str
    label: str
    value: Decimal
    unit: str
    source_layer: str
    amount_basis: str | None = None
    amount_origin: str | None = None


class DashboardTrendPointResponse(BaseModel):
    """Trend chart point response."""

    model_config = ConfigDict(from_attributes=True)

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


class DashboardBreakdownRowResponse(BaseModel):
    """Category or product breakdown response row."""

    model_config = ConfigDict(from_attributes=True)

    label: str
    revenue: Decimal
    quantity: Decimal
    transaction_count: int
    source_layer: str


class DashboardHeatmapCellResponse(BaseModel):
    """Hourly traffic heatmap response cell."""

    model_config = ConfigDict(from_attributes=True)

    weekday: int
    hour: int
    revenue: Decimal
    transaction_count: int
    source_layer: str


class DashboardCategoryTrendRowResponse(BaseModel):
    """Current vs previous period category trend response row."""

    model_config = ConfigDict(from_attributes=True)

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


class DashboardWeatherCategoryInsightRowResponse(BaseModel):
    """Category and weather insight response row."""

    model_config = ConfigDict(from_attributes=True)

    category_name: str
    weather_condition: str
    revenue: Decimal
    quantity: Decimal
    transaction_count: int
    average_temperature_c: Decimal | None
    source_layer: str


class DashboardTemperatureBandInsightRowResponse(BaseModel):
    """Temperature band insight response row."""

    model_config = ConfigDict(from_attributes=True)

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


class DashboardWeatherConditionInsightRowResponse(BaseModel):
    """Precipitation and cloudiness insight response row."""

    model_config = ConfigDict(from_attributes=True)

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


class DashboardForecastImpactRowResponse(BaseModel):
    """Forecast-aware dashboard signal response row."""

    model_config = ConfigDict(from_attributes=True)

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


class DashboardForecastCategoryDemandRowResponse(BaseModel):
    """Forecast-aware category demand response row."""

    model_config = ConfigDict(from_attributes=True)

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


class DashboardForecastPreparationRowResponse(BaseModel):
    """Forecast-aware Gourmand preparation response row."""

    model_config = ConfigDict(from_attributes=True)

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


class DashboardForecastProductDemandRowResponse(BaseModel):
    """Forecast-aware product demand response row."""

    model_config = ConfigDict(from_attributes=True)

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


class DashboardForecastPeakTimeRowResponse(BaseModel):
    """Forecast-aware peak time response row."""

    model_config = ConfigDict(from_attributes=True)

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


class DashboardFlowForecastEventRowResponse(BaseModel):
    """Forecast-aware Flow event preparation response row."""

    model_config = ConfigDict(from_attributes=True)

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


class DashboardProductRiskRowResponse(BaseModel):
    """Sellable product needing business attention response row."""

    model_config = ConfigDict(from_attributes=True)

    product_id: uuid.UUID
    product_name: str
    category_name: str
    sale_price_gross: Decimal
    estimated_unit_cost: Decimal
    estimated_margin_amount: Decimal
    estimated_margin_percent: Decimal
    risk_level: str
    risk_reasons: list[str]
    low_stock_ingredient_count: int
    missing_stock_ingredient_count: int
    source_layer: str


class DashboardStockRiskRowResponse(BaseModel):
    """Inventory item needing stock attention response row."""

    model_config = ConfigDict(from_attributes=True)

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
    risk_reasons: list[str]
    source_layer: str


class DashboardExpenseRowResponse(BaseModel):
    """Expense breakdown response row."""

    model_config = ConfigDict(from_attributes=True)

    label: str
    amount: Decimal
    gross_amount: Decimal
    net_amount: Decimal | None
    vat_amount: Decimal | None
    transaction_count: int
    source_layer: str
    amount_basis: str
    tax_breakdown_source: str


class DashboardProductDetailRowResponse(BaseModel):
    """Product drill-down response row."""

    model_config = ConfigDict(from_attributes=True)

    product_name: str
    category_name: str
    revenue: Decimal
    quantity: Decimal
    transaction_count: int
    source_layer: str


class DashboardPosSourceRowResponse(BaseModel):
    """Source POS import row behind a product drill-down."""

    model_config = ConfigDict(from_attributes=True)

    row_id: uuid.UUID
    row_number: int
    date: date | None
    receipt_no: str | None
    category_name: str
    product_name: str
    quantity: Decimal
    gross_amount: Decimal
    payment_method: str | None
    source_layer: str


class DashboardExpenseDetailRowResponse(BaseModel):
    """Expense transaction drill-down response row."""

    model_config = ConfigDict(from_attributes=True)

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


class DashboardExpenseSourceLineResponse(BaseModel):
    """Line-level source detail for an expense transaction."""

    model_config = ConfigDict(from_attributes=True)

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


class DashboardExpenseSourceResponse(BaseModel):
    """Source record behind one expense transaction."""

    model_config = ConfigDict(from_attributes=True)

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
    lines: list[DashboardExpenseSourceLineResponse]


class DashboardBasketPairRowResponse(BaseModel):
    """Frequently co-purchased product pair response row."""

    model_config = ConfigDict(from_attributes=True)

    product_a: str
    product_b: str
    basket_count: int
    total_gross_amount: Decimal
    source_layer: str


class DashboardBasketReceiptLineResponse(BaseModel):
    """One POS source row inside a receipt basket."""

    model_config = ConfigDict(from_attributes=True)

    row_id: uuid.UUID
    row_number: int
    product_name: str
    category_name: str
    quantity: Decimal
    gross_amount: Decimal
    payment_method: str | None


class DashboardBasketReceiptResponse(BaseModel):
    """Source receipt basket for one product-pair drill-down."""

    model_config = ConfigDict(from_attributes=True)

    receipt_no: str
    date: date | None
    gross_amount: Decimal
    quantity: Decimal
    lines: list[DashboardBasketReceiptLineResponse]
    source_layer: str


class DashboardResponse(BaseModel):
    """Business dashboard response."""

    model_config = ConfigDict(from_attributes=True)

    scope: str
    business_unit_id: uuid.UUID | None
    business_unit_name: str | None
    period: DashboardPeriodResponse
    kpis: list[DashboardKpiResponse]
    revenue_trend: list[DashboardTrendPointResponse]
    category_breakdown: list[DashboardBreakdownRowResponse]
    payment_method_breakdown: list[DashboardBreakdownRowResponse]
    basket_value_distribution: list[DashboardBreakdownRowResponse]
    traffic_heatmap: list[DashboardHeatmapCellResponse]
    category_trends: list[DashboardCategoryTrendRowResponse]
    weather_category_insights: list[DashboardWeatherCategoryInsightRowResponse]
    temperature_band_insights: list[DashboardTemperatureBandInsightRowResponse]
    weather_condition_insights: list[DashboardWeatherConditionInsightRowResponse]
    forecast_impact_insights: list[DashboardForecastImpactRowResponse]
    forecast_category_demand_insights: list[DashboardForecastCategoryDemandRowResponse]
    forecast_preparation_insights: list[DashboardForecastPreparationRowResponse]
    forecast_product_demand_insights: list[DashboardForecastProductDemandRowResponse]
    forecast_peak_time_insights: list[DashboardForecastPeakTimeRowResponse]
    flow_forecast_event_insights: list[DashboardFlowForecastEventRowResponse]
    product_risks: list[DashboardProductRiskRowResponse]
    stock_risks: list[DashboardStockRiskRowResponse]
    top_products: list[DashboardBreakdownRowResponse]
    expense_breakdown: list[DashboardExpenseRowResponse]
    notes: list[str]
