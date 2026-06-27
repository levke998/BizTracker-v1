"""Unit tests for POS traffic and category trend analytics."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from types import SimpleNamespace
from zoneinfo import ZoneInfo

from app.modules.analytics.infrastructure.repositories.traffic_trend_analytics_builder import (
    TrafficTrendAnalyticsBuilder,
)

TIME_ZONE = ZoneInfo("Europe/Budapest")


def _row(
    *,
    occurred_at: str,
    category: str,
    revenue: str,
    quantity: str = "1",
) -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid.uuid4(),
        normalized_payload={
            "occurred_at": occurred_at,
            "category_name": category,
            "gross_amount": revenue,
            "quantity": quantity,
        },
    )


def _builder() -> TrafficTrendAnalyticsBuilder:
    return TrafficTrendAnalyticsBuilder(
        time_zone=TIME_ZONE,
        unknown_category="Kategória nélkül",
    )


def test_heatmap_always_returns_all_weekday_hour_cells() -> None:
    rows = [
        _row(
            occurred_at="2026-06-08T10:15:00+02:00",
            category="Kávé",
            revenue="1200",
        )
    ]

    result = _builder().build_heatmap(
        rows=rows,
        start_at=datetime(2026, 6, 1, tzinfo=TIME_ZONE),
        end_at=datetime(2026, 6, 30, 23, 59, tzinfo=TIME_ZONE),
    )

    assert len(result) == 168
    monday_ten = next(row for row in result if row.weekday == 0 and row.hour == 10)
    assert monday_ten.revenue == Decimal("1200")
    assert monday_ten.transaction_count == 1


def test_category_trend_compares_equal_previous_period() -> None:
    rows = [
        _row(
            occurred_at="2026-06-02T10:00:00+02:00",
            category="Kávé",
            revenue="1000",
        ),
        _row(
            occurred_at="2026-06-09T10:00:00+02:00",
            category="Kávé",
            revenue="1800",
        ),
    ]

    result = _builder().build_category_trends(
        rows=rows,
        start_at=datetime(2026, 6, 8, tzinfo=TIME_ZONE),
        end_at=datetime(2026, 6, 14, 23, 59, 59, tzinfo=TIME_ZONE),
        limit=10,
    )

    assert len(result) == 1
    assert result[0].current_revenue == Decimal("1800")
    assert result[0].previous_revenue == Decimal("1000")
    assert result[0].revenue_change_percent == Decimal("80.0")
