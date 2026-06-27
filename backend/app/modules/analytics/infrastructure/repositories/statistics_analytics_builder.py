"""Dashboard descriptive statistics and data-quality read-model builder."""

from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, time
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any
from zoneinfo import ZoneInfo

from app.modules.analytics.domain.entities.dashboard_snapshot import (
    DashboardStatisticsQuality,
)
from app.modules.imports.infrastructure.orm.import_row_model import ImportRowModel


class DashboardStatisticsAnalyticsBuilder:
    """Build explainable statistics for Dashboard 2.0 decision support."""

    def __init__(self, *, time_zone: ZoneInfo) -> None:
        self._time_zone = time_zone

    def build_quality(
        self,
        *,
        rows: list[ImportRowModel],
        start_at: datetime,
        end_at: datetime,
    ) -> DashboardStatisticsQuality:
        daily_revenue: dict[date, Decimal] = defaultdict(lambda: Decimal("0"))
        baskets: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
        pos_row_count = 0

        for row in rows:
            payload = row.normalized_payload or {}
            occurred_at = self._payload_occurred_at(payload)
            if occurred_at is None or occurred_at < start_at or occurred_at > end_at:
                continue

            gross_amount = self._parse_decimal(payload.get("gross_amount"))
            business_date = occurred_at.astimezone(self._time_zone).date()
            daily_revenue[business_date] += gross_amount
            baskets[self._basket_key(row, payload)] += gross_amount
            pos_row_count += 1

        daily_values = list(daily_revenue.values())
        basket_values = list(baskets.values())
        period_day_count = max((end_at.date() - start_at.date()).days + 1, 1)
        active_sales_day_count = len(daily_values)
        coverage_percent = self._percent(
            Decimal(active_sales_day_count),
            Decimal(period_day_count),
        )
        quality_level = self._quality_level(
            active_sales_day_count=active_sales_day_count,
            basket_count=len(basket_values),
            coverage_percent=coverage_percent,
        )

        return DashboardStatisticsQuality(
            period_day_count=period_day_count,
            active_sales_day_count=active_sales_day_count,
            pos_row_count=pos_row_count,
            basket_count=len(basket_values),
            coverage_percent=coverage_percent,
            quality_level=quality_level,
            average_daily_revenue=self._average(daily_values),
            median_daily_revenue=self._quantile(daily_values, Decimal("0.50")),
            p25_daily_revenue=self._quantile(daily_values, Decimal("0.25")),
            p75_daily_revenue=self._quantile(daily_values, Decimal("0.75")),
            p90_daily_revenue=self._quantile(daily_values, Decimal("0.90")),
            p95_daily_revenue=self._quantile(daily_values, Decimal("0.95")),
            average_basket_value=self._average(basket_values),
            median_basket_value=self._quantile(basket_values, Decimal("0.50")),
            p25_basket_value=self._quantile(basket_values, Decimal("0.25")),
            p75_basket_value=self._quantile(basket_values, Decimal("0.75")),
            p90_basket_value=self._quantile(basket_values, Decimal("0.90")),
            p95_basket_value=self._quantile(basket_values, Decimal("0.95")),
            recommendation=self._recommendation(
                quality_level=quality_level,
                active_sales_day_count=active_sales_day_count,
                basket_count=len(basket_values),
            ),
            source_layer="pos_import_statistics",
        )

    def _payload_occurred_at(self, payload: dict[str, Any]) -> datetime | None:
        occurred_at = payload.get("occurred_at")
        if isinstance(occurred_at, str):
            try:
                parsed = datetime.fromisoformat(occurred_at)
            except ValueError:
                parsed = None
            if parsed is not None:
                if parsed.tzinfo is None:
                    parsed = parsed.replace(tzinfo=self._time_zone)
                return parsed.astimezone(self._time_zone)

        payload_date = self._parse_payload_date(payload.get("date"))
        if payload_date is None:
            return None
        return datetime.combine(payload_date, time.min, tzinfo=self._time_zone)

    @staticmethod
    def _parse_payload_date(value: Any) -> date | None:
        if isinstance(value, date) and not isinstance(value, datetime):
            return value
        if isinstance(value, str):
            try:
                return date.fromisoformat(value)
            except ValueError:
                return None
        return None

    @staticmethod
    def _parse_decimal(value: Any) -> Decimal:
        try:
            return Decimal(str(value or "0"))
        except (InvalidOperation, ValueError):
            return Decimal("0")

    @staticmethod
    def _basket_key(row: ImportRowModel, payload: dict[str, Any]) -> str:
        receipt_no = payload.get("receipt_no")
        if isinstance(receipt_no, str) and receipt_no.strip():
            return receipt_no.strip()
        return str(row.id)

    @staticmethod
    def _average(values: list[Decimal]) -> Decimal:
        if not values:
            return Decimal("0")
        return (sum(values, Decimal("0")) / Decimal(len(values))).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )

    @staticmethod
    def _quantile(values: list[Decimal], quantile: Decimal) -> Decimal:
        if not values:
            return Decimal("0")
        ordered = sorted(values)
        if len(ordered) == 1:
            return ordered[0].quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        position = int(
            (
                (Decimal(len(ordered) - 1) * quantile).to_integral_value(
                    rounding=ROUND_HALF_UP,
                )
            )
        )
        return ordered[position].quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @staticmethod
    def _percent(numerator: Decimal, denominator: Decimal) -> Decimal:
        if denominator <= Decimal("0"):
            return Decimal("0")
        return (numerator / denominator * Decimal("100")).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )

    @staticmethod
    def _quality_level(
        *,
        active_sales_day_count: int,
        basket_count: int,
        coverage_percent: Decimal,
    ) -> str:
        if (
            active_sales_day_count >= 21
            and basket_count >= 300
            and coverage_percent >= 70
        ):
            return "strong"
        if (
            active_sales_day_count >= 10
            and basket_count >= 100
            and coverage_percent >= 40
        ):
            return "usable"
        if active_sales_day_count >= 3 and basket_count >= 20:
            return "limited"
        return "insufficient"

    @staticmethod
    def _recommendation(
        *,
        quality_level: str,
        active_sales_day_count: int,
        basket_count: int,
    ) -> str:
        if quality_level == "strong":
            return "Stabil statisztikai alap: median, percentilis es baseline forecast dontestamogatasra hasznalhato."
        if quality_level == "usable":
            return "Hasznalhato statisztikai alap: baseline forecast indithato, de confidence jeloles kotelezo."
        if quality_level == "limited":
            return "Korlatozott minta: leiro statisztikara alkalmas, kovetkezteteshez es forecasthez ovatosan hasznalhato."
        return (
            "Nincs eleg tiszta historikus minta. Elobb import, mapping, AFA es "
            "forgalmi lefedettseg szukseges."
        )
