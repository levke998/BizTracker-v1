"""Analytics repository contract."""

from __future__ import annotations

import uuid
from datetime import date
from typing import Protocol

from app.modules.analytics.domain.entities.dashboard_snapshot import (
    DashboardBreakdownRow,
    DashboardExpenseDetailRow,
    DashboardProductDetailRow,
    DashboardSnapshot,
)


class AnalyticsRepository(Protocol):
    """Defines read-model access for business dashboards."""

    def get_business_dashboard(
        self,
        *,
        scope: str,
        business_unit_id: uuid.UUID | None,
        preset: str,
        start_date: date,
        end_date: date,
        grain: str,
    ) -> DashboardSnapshot:
        """Return one aggregated dashboard snapshot."""

    def list_category_breakdown(
        self,
        *,
        scope: str,
        business_unit_id: uuid.UUID | None,
        start_date: date,
        end_date: date,
    ) -> list[DashboardBreakdownRow]:
        """Return category revenue breakdown for a dashboard period."""

    def list_product_breakdown(
        self,
        *,
        scope: str,
        business_unit_id: uuid.UUID | None,
        start_date: date,
        end_date: date,
        category_name: str | None = None,
    ) -> list[DashboardProductDetailRow]:
        """Return product revenue breakdown for a dashboard period."""

    def list_expense_details(
        self,
        *,
        scope: str,
        business_unit_id: uuid.UUID | None,
        start_date: date,
        end_date: date,
        transaction_type: str | None = None,
    ) -> list[DashboardExpenseDetailRow]:
        """Return expense transaction details for a dashboard period."""
