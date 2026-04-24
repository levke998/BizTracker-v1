"""Get business dashboard data query."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta

from app.modules.analytics.domain.entities.dashboard_snapshot import (
    DashboardBreakdownRow,
    DashboardExpenseDetailRow,
    DashboardProductDetailRow,
    DashboardSnapshot,
)
from app.modules.analytics.domain.repositories.analytics_repository import (
    AnalyticsRepository,
)

SUPPORTED_SCOPES = {"overall", "flow", "gourmand"}
SUPPORTED_PRESETS = {
    "today",
    "week",
    "month",
    "year",
    "last_7_days",
    "last_30_days",
    "custom",
}
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
            start_date=resolved_start,
            end_date=resolved_end,
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
            start_date=resolved_start,
            end_date=resolved_end,
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
            start_date=resolved_start,
            end_date=resolved_end,
            category_name=category_name.strip() if category_name else None,
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
            start_date=resolved_start,
            end_date=resolved_end,
            transaction_type=transaction_type.strip() if transaction_type else None,
        )

def _normalize_scope(scope: str) -> str:
    normalized_scope = scope.strip().lower()
    if normalized_scope not in SUPPORTED_SCOPES:
        raise DashboardScopeError(f"Unsupported dashboard scope: {scope}.")
    return normalized_scope


def _resolve_period(period: DashboardPeriodInput) -> tuple[date, date, str]:
    preset = period.preset.strip().lower()
    if preset not in SUPPORTED_PRESETS:
        raise DashboardPeriodError(f"Unsupported dashboard period: {period.preset}.")

    today = datetime.now(UTC).date()

    if preset == "today":
        return today, today, "day"
    if preset == "week":
        start = today - timedelta(days=today.weekday())
        return start, today, "day"
    if preset == "month":
        return today.replace(day=1), today, "day"
    if preset == "year":
        return today.replace(month=1, day=1), today, "month"
    if preset == "last_7_days":
        return today - timedelta(days=6), today, "day"
    if preset == "last_30_days":
        return today - timedelta(days=29), today, "day"

    if period.start_date is None or period.end_date is None:
        raise DashboardPeriodError(
            "Custom dashboard period requires start_date and end_date."
        )
    if period.start_date > period.end_date:
        raise DashboardPeriodError("Dashboard start_date must be before end_date.")

    delta_days = (period.end_date - period.start_date).days
    grain = "month" if delta_days > 120 else "day"
    return period.start_date, period.end_date, grain
