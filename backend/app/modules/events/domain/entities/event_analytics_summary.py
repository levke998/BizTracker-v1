"""Event analytics summary read-model entities."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class EventAnalyticsMetrics:
    """Aggregated event analytics metrics for one filtered period."""

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


@dataclass(frozen=True, slots=True)
class EventAnalyticsHighlight:
    """One highlighted event selected by a business metric."""

    event_id: uuid.UUID | None
    title: str | None
    performer_name: str | None
    starts_at: datetime | None
    metric_value: Decimal | None


@dataclass(frozen=True, slots=True)
class EventPerformerAnalyticsRow:
    """Aggregated performance row for one performer."""

    performer: str
    event_count: int
    ticket_revenue_gross: Decimal
    bar_revenue_gross: Decimal
    own_revenue: Decimal
    event_profit_lite: Decimal


@dataclass(frozen=True, slots=True)
class EventAnalyticsInsight:
    """Business-facing decision signal for the event analyzer."""

    key: str
    tone: str
    title: str
    event_id: uuid.UUID
    event_title: str
    metric: str
    detail: str


@dataclass(frozen=True, slots=True)
class EventAnalyticsHighlights:
    """Selected top events for the analyzer summary cards."""

    top_profit: EventAnalyticsHighlight
    most_popular: EventAnalyticsHighlight
    highest_revenue: EventAnalyticsHighlight
    top_margin: EventAnalyticsHighlight
    highest_cost_ratio: EventAnalyticsHighlight


@dataclass(frozen=True, slots=True)
class EventAnalyticsSummary:
    """Complete event analyzer read model."""

    metrics: EventAnalyticsMetrics
    highlights: EventAnalyticsHighlights
    performer_rows: tuple[EventPerformerAnalyticsRow, ...]
    insights: tuple[EventAnalyticsInsight, ...]
