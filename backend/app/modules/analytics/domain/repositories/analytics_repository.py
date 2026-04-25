"""Analytics repository contract."""

from __future__ import annotations

import uuid
from datetime import date
from typing import Protocol

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

    def list_product_source_rows(
        self,
        *,
        scope: str,
        business_unit_id: uuid.UUID | None,
        start_date: date,
        end_date: date,
        product_name: str,
        category_name: str | None = None,
        limit: int = 50,
    ) -> list[DashboardPosSourceRow]:
        """Return source POS rows behind one product drill-down."""

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

    def get_expense_source(
        self,
        *,
        transaction_id: uuid.UUID,
    ) -> DashboardExpenseSource | None:
        """Return the source record behind one expense transaction."""

    def list_basket_pairs(
        self,
        *,
        scope: str,
        business_unit_id: uuid.UUID | None,
        start_date: date,
        end_date: date,
        limit: int = 20,
    ) -> list[DashboardBasketPairRow]:
        """Return frequently co-purchased product pairs from POS receipts."""

    def list_basket_pair_receipts(
        self,
        *,
        scope: str,
        business_unit_id: uuid.UUID | None,
        start_date: date,
        end_date: date,
        product_a: str,
        product_b: str,
        limit: int = 20,
    ) -> list[DashboardBasketReceipt]:
        """Return source receipt baskets containing a product pair."""
