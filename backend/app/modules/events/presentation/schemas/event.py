"""Event request and response schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class EventCreateRequest(BaseModel):
    """Create/update payload for one event."""

    business_unit_id: uuid.UUID
    location_id: uuid.UUID | None = None
    title: str = Field(min_length=1, max_length=180)
    status: str = Field(default="planned", max_length=30)
    starts_at: datetime
    ends_at: datetime | None = None
    performer_name: str | None = Field(default=None, max_length=180)
    expected_attendance: int | None = Field(default=None, ge=0)
    ticket_revenue_gross: Decimal = Field(default=Decimal("0"), ge=0)
    bar_revenue_gross: Decimal = Field(default=Decimal("0"), ge=0)
    performer_settlement_type: str = Field(default="hybrid", max_length=40)
    performer_share_percent: Decimal = Field(default=Decimal("80"), ge=0, le=100)
    performer_fixed_fee: Decimal = Field(default=Decimal("0"), ge=0)
    event_cost_amount: Decimal = Field(default=Decimal("0"), ge=0)
    notes: str | None = Field(default=None, max_length=1000)
    is_active: bool = True


class EventResponse(BaseModel):
    """Read model for one event."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    business_unit_id: uuid.UUID
    location_id: uuid.UUID | None
    title: str
    status: str
    starts_at: datetime
    ends_at: datetime | None
    performer_name: str | None
    expected_attendance: int | None
    ticket_revenue_gross: Decimal
    bar_revenue_gross: Decimal
    performer_settlement_type: str
    performer_share_percent: Decimal
    performer_fixed_fee: Decimal
    event_cost_amount: Decimal
    notes: str | None
    is_active: bool
    performer_share_amount: Decimal
    performer_fixed_fee_amount: Decimal
    performer_total_compensation_gross: Decimal
    retained_ticket_revenue: Decimal
    own_revenue: Decimal
    event_profit_lite: Decimal
    created_at: datetime
    updated_at: datetime


class EventPerformanceCategoryResponse(BaseModel):
    """Aggregated POS revenue for one event category."""

    model_config = ConfigDict(from_attributes=True)

    category_name: str
    gross_amount: Decimal
    quantity: Decimal
    row_count: int


class EventPerformanceProductResponse(BaseModel):
    """Aggregated POS revenue for one event product."""

    model_config = ConfigDict(from_attributes=True)

    product_name: str
    category_name: str
    gross_amount: Decimal
    quantity: Decimal
    row_count: int


class EventWeatherSummaryResponse(BaseModel):
    """Weather context over the event time window."""

    model_config = ConfigDict(from_attributes=True)

    observation_count: int
    dominant_condition: str | None
    average_temperature_c: Decimal | None
    total_precipitation_mm: Decimal
    average_cloud_cover_percent: Decimal | None
    average_wind_speed_kmh: Decimal | None


class EventWeatherCoverageResponse(BaseModel):
    """Weather cache preparation result for one event window."""

    model_config = ConfigDict(from_attributes=True)

    status: str
    reason: str | None
    start_at: datetime
    end_at: datetime
    requested_hours: int
    cached_hours: int
    missing_hours: int
    backfill_attempted: bool
    created_count: int
    updated_count: int
    skipped_count: int


class EventTicketActualRequest(BaseModel):
    """Manual ticket-system actual payload for one event."""

    source_name: str | None = Field(default=None, max_length=120)
    source_reference: str | None = Field(default=None, max_length=180)
    sold_quantity: Decimal = Field(default=Decimal("0"), ge=0)
    gross_revenue: Decimal = Field(default=Decimal("0"), ge=0)
    net_revenue: Decimal | None = Field(default=None, ge=0)
    vat_amount: Decimal | None = Field(default=None, ge=0)
    vat_rate_id: uuid.UUID | None = None
    platform_fee_gross: Decimal = Field(default=Decimal("0"), ge=0)
    reported_at: datetime | None = None
    notes: str | None = Field(default=None, max_length=1000)


class EventTicketActualResponse(BaseModel):
    """Read model for ticket-system actuals attached to one event."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    event_id: uuid.UUID
    source_name: str | None
    source_reference: str | None
    sold_quantity: Decimal
    gross_revenue: Decimal
    net_revenue: Decimal | None
    vat_amount: Decimal | None
    vat_rate_id: uuid.UUID | None
    platform_fee_gross: Decimal
    reported_at: datetime | None
    notes: str | None
    created_at: datetime
    updated_at: datetime


class EventCostLineRequest(BaseModel):
    """Manual event cost line payload."""

    category: str = Field(default="egyeb", max_length=80)
    description: str = Field(min_length=1, max_length=240)
    amount_gross: Decimal = Field(ge=0)
    source_type: str = Field(default="manual", max_length=40)
    source_reference: str | None = Field(default=None, max_length=180)
    incurred_at: datetime | None = None
    notes: str | None = Field(default=None, max_length=1000)


class ReplaceEventCostLinesRequest(BaseModel):
    """Replace all cost lines attached to one event."""

    cost_lines: list[EventCostLineRequest] = Field(default_factory=list, max_length=100)


class EventCostLineResponse(BaseModel):
    """Read model for one event cost line."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    event_id: uuid.UUID
    category: str
    description: str
    amount_gross: Decimal
    source_type: str
    source_reference: str | None
    incurred_at: datetime | None
    notes: str | None
    created_at: datetime
    updated_at: datetime


class EventPerformanceResponse(BaseModel):
    """POS and weather performance attached to an event time window."""

    model_config = ConfigDict(from_attributes=True)

    event_id: uuid.UUID
    business_unit_id: uuid.UUID
    starts_at: datetime
    ends_at: datetime
    source_row_count: int
    receipt_count: int
    ticket_revenue_gross: Decimal
    bar_revenue_gross: Decimal
    total_revenue_gross: Decimal
    ticket_quantity: Decimal
    bar_quantity: Decimal
    performer_settlement_type: str
    performer_share_percent: Decimal
    performer_share_amount: Decimal
    performer_fixed_fee_amount: Decimal
    performer_total_compensation_gross: Decimal
    retained_ticket_revenue: Decimal
    platform_fee_gross: Decimal
    event_cost_lines_gross: Decimal
    own_revenue: Decimal
    operating_cost_gross: Decimal
    event_profit_lite: Decimal
    event_profit_margin_percent: Decimal | None
    operating_cost_ratio_percent: Decimal | None
    ticket_revenue_share_percent: Decimal | None
    bar_revenue_share_percent: Decimal | None
    profit_status: str
    ticket_revenue_source: str
    settlement_status: str
    categories: tuple[EventPerformanceCategoryResponse, ...]
    top_products: tuple[EventPerformanceProductResponse, ...]
    weather: EventWeatherSummaryResponse


class EventAnalyticsMetricsResponse(BaseModel):
    """Aggregated event analytics metrics for one filtered period."""

    model_config = ConfigDict(from_attributes=True)

    event_count: int
    ticket_revenue_gross: Decimal
    bar_revenue_gross: Decimal
    own_revenue: Decimal
    event_profit_lite: Decimal
    receipt_count: int
    ticket_actual_count: int
    missing_ticket_actual_count: int
    ticket_actual_coverage_percent: Decimal
    profitable_count: int
    loss_count: int


class EventAnalyticsHighlightResponse(BaseModel):
    """One highlighted event selected by a business metric."""

    model_config = ConfigDict(from_attributes=True)

    event_id: uuid.UUID | None
    title: str | None
    performer_name: str | None
    starts_at: datetime | None
    metric_value: Decimal | None


class EventAnalyticsHighlightsResponse(BaseModel):
    """Selected top events for the analyzer summary cards."""

    model_config = ConfigDict(from_attributes=True)

    top_profit: EventAnalyticsHighlightResponse
    most_popular: EventAnalyticsHighlightResponse
    highest_revenue: EventAnalyticsHighlightResponse
    top_margin: EventAnalyticsHighlightResponse
    highest_cost_ratio: EventAnalyticsHighlightResponse


class EventPerformerAnalyticsRowResponse(BaseModel):
    """Aggregated performance row for one performer."""

    model_config = ConfigDict(from_attributes=True)

    performer: str
    event_count: int
    ticket_revenue_gross: Decimal
    bar_revenue_gross: Decimal
    own_revenue: Decimal
    event_profit_lite: Decimal


class EventAnalyticsInsightResponse(BaseModel):
    """Business-facing decision signal for the event analyzer."""

    model_config = ConfigDict(from_attributes=True)

    key: str
    tone: str
    title: str
    event_id: uuid.UUID
    event_title: str
    metric: str
    detail: str


class EventAnalyticsSummaryResponse(BaseModel):
    """Complete event analyzer read model."""

    model_config = ConfigDict(from_attributes=True)

    metrics: EventAnalyticsMetricsResponse
    highlights: EventAnalyticsHighlightsResponse
    performer_rows: tuple[EventPerformerAnalyticsRowResponse, ...]
    insights: tuple[EventAnalyticsInsightResponse, ...]
