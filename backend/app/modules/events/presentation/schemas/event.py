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
    performer_share_percent: Decimal
    performer_fixed_fee: Decimal
    event_cost_amount: Decimal
    notes: str | None
    is_active: bool
    performer_share_amount: Decimal
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
    performer_share_percent: Decimal
    performer_share_amount: Decimal
    retained_ticket_revenue: Decimal
    own_revenue: Decimal
    event_profit_lite: Decimal
    categories: tuple[EventPerformanceCategoryResponse, ...]
    top_products: tuple[EventPerformanceProductResponse, ...]
    weather: EventWeatherSummaryResponse
