"""POS traffic heatmap and category trend read-model builder."""

from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from typing import Any
from zoneinfo import ZoneInfo

from app.modules.analytics.domain.entities.dashboard_snapshot import (
    DashboardCategoryTrendRow,
    DashboardHeatmapCell,
)
from app.modules.imports.infrastructure.orm.import_row_model import ImportRowModel


class TrafficTrendAnalyticsBuilder:
    """Build time and category comparisons from normalized POS rows."""

    def __init__(self, *, time_zone: ZoneInfo, unknown_category: str) -> None:
        self._time_zone = time_zone
        self._unknown_category = unknown_category

    def build_heatmap(
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
            aggregate[key]["revenue"] += self._parse_decimal(
                payload.get("gross_amount")
            )
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

    def build_category_trends(
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
        trends = [
            self._trend_row(
                label=label,
                current=current.get(label, self._empty_aggregate()),
                previous=previous.get(label, self._empty_aggregate()),
            )
            for label in set(current) | set(previous)
        ]
        return sorted(
            trends,
            key=lambda row: (abs(row.revenue_change), row.current_revenue),
            reverse=True,
        )[:limit]

    def _aggregate_categories(
        self,
        *,
        rows: list[ImportRowModel],
        start_at: datetime,
        end_at: datetime,
    ) -> dict[str, dict[str, Decimal | int]]:
        aggregate: dict[str, dict[str, Decimal | int]] = defaultdict(
            self._empty_aggregate
        )
        for row in rows:
            payload = row.normalized_payload or {}
            occurred_at = self._payload_occurred_at(payload)
            if occurred_at is None or occurred_at < start_at or occurred_at > end_at:
                continue
            label = self._extract_text(
                payload.get("category_name"),
                fallback=self._unknown_category,
            )
            aggregate[label]["revenue"] += self._parse_decimal(
                payload.get("gross_amount")
            )
            aggregate[label]["quantity"] += self._parse_decimal(payload.get("quantity"))
            aggregate[label]["count"] += 1
        return dict(aggregate)

    @staticmethod
    def _trend_row(
        *,
        label: str,
        current: dict[str, Decimal | int],
        previous: dict[str, Decimal | int],
    ) -> DashboardCategoryTrendRow:
        current_revenue = Decimal(current["revenue"])
        previous_revenue = Decimal(previous["revenue"])
        change = current_revenue - previous_revenue
        change_percent = (
            change / previous_revenue * Decimal("100")
            if previous_revenue > Decimal("0")
            else (Decimal("100") if current_revenue > Decimal("0") else Decimal("0"))
        )
        return DashboardCategoryTrendRow(
            label=label,
            current_revenue=current_revenue,
            previous_revenue=previous_revenue,
            revenue_change=change,
            revenue_change_percent=change_percent,
            current_quantity=Decimal(current["quantity"]),
            previous_quantity=Decimal(previous["quantity"]),
            current_transaction_count=int(current["count"]),
            previous_transaction_count=int(previous["count"]),
            source_layer="import_derived",
        )

    def _payload_occurred_at(self, payload: dict[str, Any]) -> datetime | None:
        value = payload.get("occurred_at")
        if isinstance(value, str):
            try:
                parsed = datetime.fromisoformat(value)
            except ValueError:
                parsed = None
            if parsed is not None:
                return (
                    parsed.replace(tzinfo=self._time_zone)
                    if parsed.tzinfo is None
                    else parsed.astimezone(self._time_zone)
                )
        value = payload.get("date")
        if not isinstance(value, str):
            return None
        try:
            parsed_date = date.fromisoformat(value)
        except ValueError:
            return None
        return datetime(
            parsed_date.year,
            parsed_date.month,
            parsed_date.day,
            tzinfo=self._time_zone,
        )

    @staticmethod
    def _empty_aggregate() -> dict[str, Decimal | int]:
        return {"revenue": Decimal("0"), "quantity": Decimal("0"), "count": 0}

    @staticmethod
    def _parse_decimal(value: Any) -> Decimal:
        if value is None:
            return Decimal("0")
        try:
            return Decimal(str(value))
        except (InvalidOperation, ValueError):
            return Decimal("0")

    @staticmethod
    def _extract_text(value: Any, *, fallback: str) -> str:
        if isinstance(value, str) and value.strip():
            return value.strip()
        return fallback
