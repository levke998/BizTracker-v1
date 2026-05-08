"""Event performance read-model entities."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class EventPerformanceCategoryRow:
    """Aggregated POS revenue for one event category."""

    category_name: str
    gross_amount: Decimal
    quantity: Decimal
    row_count: int


@dataclass(frozen=True, slots=True)
class EventPerformanceProductRow:
    """Aggregated POS revenue for one event product."""

    product_name: str
    category_name: str
    gross_amount: Decimal
    quantity: Decimal
    row_count: int


@dataclass(frozen=True, slots=True)
class EventWeatherSummary:
    """Weather context over the event time window."""

    observation_count: int
    dominant_condition: str | None
    average_temperature_c: Decimal | None
    total_precipitation_mm: Decimal
    average_cloud_cover_percent: Decimal | None
    average_wind_speed_kmh: Decimal | None


@dataclass(frozen=True, slots=True)
class EventPerformance:
    """POS and weather performance attached to an event time window."""

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
    categories: tuple[EventPerformanceCategoryRow, ...]
    top_products: tuple[EventPerformanceProductRow, ...]
    weather: EventWeatherSummary
