"""Get business dashboard data query."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from app.modules.analytics.domain.entities.dashboard_snapshot import (
    DashboardBasketPairRow,
    DashboardBasketReceipt,
    DashboardBreakdownRow,
    DashboardExpenseDetailRow,
    DashboardExpenseSource,
    DashboardPosSourceRow,
    DashboardProductDetailRow,
    DashboardSnapshot,
)
from app.modules.analytics.domain.repositories.analytics_repository import (
    AnalyticsRepository,
)

SUPPORTED_SCOPES = {"overall", "flow", "gourmand"}
SUPPORTED_PRESETS = {
    "last_1_hour",
    "last_6_hours",
    "last_12_hours",
    "today",
    "week",
    "month",
    "year",
    "last_7_days",
    "last_30_days",
    "custom",
}
APP_TIME_ZONE = ZoneInfo("Europe/Budapest")
class DashboardScopeError(ValueError):
    """Raised when an unsupported dashboard scope is requested."""


class DashboardPeriodError(ValueError):
    """Raised when the dashboard period cannot be resolved."""


@dataclass(frozen=True, slots=True)
class DashboardPeriodInput:
    """Raw period request coming from the API layer."""

    preset: str
    start_date: date | None
    end_date: date | None


@dataclass(slots=True)
class GetDashboardDataQuery:
    """Resolve dashboard filters and delegate aggregation to the repository."""

    repository: AnalyticsRepository

    def execute(
        self,
        *,
        scope: str,
        business_unit_id: uuid.UUID | None,
        period: DashboardPeriodInput,
    ) -> DashboardSnapshot:
        normalized_scope = _normalize_scope(scope)
        resolved_start, resolved_end, grain = _resolve_period(period)

        return self.repository.get_business_dashboard(
            scope=normalized_scope,
            business_unit_id=business_unit_id,
            preset=period.preset.strip().lower(),
            start_at=resolved_start,
            end_at=resolved_end,
            grain=grain,
        )


@dataclass(slots=True)
class ListDashboardCategoryBreakdownQuery:
    """Return category drill-down rows for one dashboard context."""

    repository: AnalyticsRepository

    def execute(
        self,
        *,
        scope: str,
        business_unit_id: uuid.UUID | None,
        period: DashboardPeriodInput,
    ) -> list[DashboardBreakdownRow]:
        normalized_scope = _normalize_scope(scope)
        resolved_start, resolved_end, _grain = _resolve_period(period)
        return self.repository.list_category_breakdown(
            scope=normalized_scope,
            business_unit_id=business_unit_id,
            start_at=resolved_start,
            end_at=resolved_end,
        )


@dataclass(slots=True)
class ListDashboardProductBreakdownQuery:
    """Return product drill-down rows for one dashboard context."""

    repository: AnalyticsRepository

    def execute(
        self,
        *,
        scope: str,
        business_unit_id: uuid.UUID | None,
        period: DashboardPeriodInput,
        category_name: str | None,
    ) -> list[DashboardProductDetailRow]:
        normalized_scope = _normalize_scope(scope)
        resolved_start, resolved_end, _grain = _resolve_period(period)
        return self.repository.list_product_breakdown(
            scope=normalized_scope,
            business_unit_id=business_unit_id,
            start_at=resolved_start,
            end_at=resolved_end,
            category_name=category_name.strip() if category_name else None,
        )


@dataclass(slots=True)
class ListDashboardProductSourceRowsQuery:
    """Return source POS rows for one selected dashboard product."""

    repository: AnalyticsRepository

    def execute(
        self,
        *,
        scope: str,
        business_unit_id: uuid.UUID | None,
        period: DashboardPeriodInput,
        product_name: str,
        category_name: str | None,
        limit: int,
    ) -> list[DashboardPosSourceRow]:
        normalized_scope = _normalize_scope(scope)
        resolved_start, resolved_end, _grain = _resolve_period(period)
        normalized_product_name = product_name.strip()
        if not normalized_product_name:
            raise DashboardPeriodError("Product name is required.")
        return self.repository.list_product_source_rows(
            scope=normalized_scope,
            business_unit_id=business_unit_id,
            start_at=resolved_start,
            end_at=resolved_end,
            product_name=normalized_product_name,
            category_name=category_name.strip() if category_name else None,
            limit=limit,
        )


@dataclass(slots=True)
class ListDashboardExpenseDetailsQuery:
    """Return expense transaction rows for one dashboard context."""

    repository: AnalyticsRepository

    def execute(
        self,
        *,
        scope: str,
        business_unit_id: uuid.UUID | None,
        period: DashboardPeriodInput,
        transaction_type: str | None,
    ) -> list[DashboardExpenseDetailRow]:
        normalized_scope = _normalize_scope(scope)
        resolved_start, resolved_end, _grain = _resolve_period(period)
        return self.repository.list_expense_details(
            scope=normalized_scope,
            business_unit_id=business_unit_id,
            start_at=resolved_start,
            end_at=resolved_end,
            transaction_type=transaction_type.strip() if transaction_type else None,
        )


@dataclass(slots=True)
class GetDashboardExpenseSourceQuery:
    """Return source detail for one dashboard expense transaction."""

    repository: AnalyticsRepository

    def execute(self, *, transaction_id: uuid.UUID) -> DashboardExpenseSource | None:
        return self.repository.get_expense_source(transaction_id=transaction_id)


@dataclass(slots=True)
class ListDashboardBasketPairsQuery:
    """Return frequently co-purchased product pairs for one dashboard context."""

    repository: AnalyticsRepository

    def execute(
        self,
        *,
        scope: str,
        business_unit_id: uuid.UUID | None,
        period: DashboardPeriodInput,
        limit: int,
    ) -> list[DashboardBasketPairRow]:
        normalized_scope = _normalize_scope(scope)
        resolved_start, resolved_end, _grain = _resolve_period(period)
        return self.repository.list_basket_pairs(
            scope=normalized_scope,
            business_unit_id=business_unit_id,
            start_at=resolved_start,
            end_at=resolved_end,
            limit=limit,
        )


@dataclass(slots=True)
class ListDashboardBasketPairReceiptsQuery:
    """Return source receipt baskets for one co-purchased product pair."""

    repository: AnalyticsRepository

    def execute(
        self,
        *,
        scope: str,
        business_unit_id: uuid.UUID | None,
        period: DashboardPeriodInput,
        product_a: str,
        product_b: str,
        limit: int,
    ) -> list[DashboardBasketReceipt]:
        normalized_scope = _normalize_scope(scope)
        resolved_start, resolved_end, _grain = _resolve_period(period)
        normalized_product_a = product_a.strip()
        normalized_product_b = product_b.strip()
        if not normalized_product_a or not normalized_product_b:
            raise DashboardPeriodError("Both product names are required.")
        return self.repository.list_basket_pair_receipts(
            scope=normalized_scope,
            business_unit_id=business_unit_id,
            start_at=resolved_start,
            end_at=resolved_end,
            product_a=normalized_product_a,
            product_b=normalized_product_b,
            limit=limit,
        )


def _normalize_scope(scope: str) -> str:
    normalized_scope = scope.strip().lower()
    if normalized_scope not in SUPPORTED_SCOPES:
        raise DashboardScopeError(f"Unsupported dashboard scope: {scope}.")
    return normalized_scope


def _resolve_period(period: DashboardPeriodInput) -> tuple[datetime, datetime, str]:
    preset = period.preset.strip().lower()
    if preset not in SUPPORTED_PRESETS:
        raise DashboardPeriodError(f"Unsupported dashboard period: {period.preset}.")

    now = datetime.now(APP_TIME_ZONE)
    today = now.date()

    if preset == "last_1_hour":
        return now - timedelta(hours=1), now, "hour"
    if preset == "last_6_hours":
        return now - timedelta(hours=6), now, "hour"
    if preset == "last_12_hours":
        return now - timedelta(hours=12), now, "hour"
    if preset == "today":
        return _day_start(today), now, "hour"
    if preset == "week":
        start = today - timedelta(days=today.weekday())
        return _day_start(start), _day_end(today), "day"
    if preset == "month":
        return _day_start(today.replace(day=1)), _day_end(today), "day"
    if preset == "year":
        return _day_start(today.replace(month=1, day=1)), _day_end(today), "month"
    if preset == "last_7_days":
        return _day_start(today - timedelta(days=6)), _day_end(today), "day"
    if preset == "last_30_days":
        return _day_start(today - timedelta(days=29)), _day_end(today), "day"

    if period.start_date is None or period.end_date is None:
        raise DashboardPeriodError(
            "Custom dashboard period requires start_date and end_date."
        )
    if period.start_date > period.end_date:
        raise DashboardPeriodError("Dashboard start_date must be before end_date.")

    delta_days = (period.end_date - period.start_date).days
    grain = "month" if delta_days > 120 else "day"
    return _day_start(period.start_date), _day_end(period.end_date), grain


def _day_start(value: date) -> datetime:
    return datetime.combine(value, datetime.min.time(), tzinfo=APP_TIME_ZONE)


def _day_end(value: date) -> datetime:
    return datetime.combine(value, datetime.max.time(), tzinfo=APP_TIME_ZONE)
