"""Analytics presentation dependency wiring."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.modules.analytics.application.queries.get_dashboard_data import (
    GetDashboardDataQuery,
    GetDashboardExpenseSourceQuery,
    ListDashboardBasketPairReceiptsQuery,
    ListDashboardBasketPairsQuery,
    ListDashboardCategoryBreakdownQuery,
    ListDashboardExpenseDetailsQuery,
    ListDashboardProductBreakdownQuery,
    ListDashboardProductSourceRowsQuery,
)
from app.modules.analytics.infrastructure.repositories.sqlalchemy_analytics_repository import (
    SqlAlchemyAnalyticsRepository,
)

DbSession = Annotated[Session, Depends(get_db_session)]


def get_dashboard_data_query(session: DbSession) -> GetDashboardDataQuery:
    """Wire dashboard query to the analytics repository."""

    repository = SqlAlchemyAnalyticsRepository(session)
    return GetDashboardDataQuery(repository=repository)


def get_dashboard_category_breakdown_query(
    session: DbSession,
) -> ListDashboardCategoryBreakdownQuery:
    """Wire category drill-down query to the analytics repository."""

    repository = SqlAlchemyAnalyticsRepository(session)
    return ListDashboardCategoryBreakdownQuery(repository=repository)


def get_dashboard_product_breakdown_query(
    session: DbSession,
) -> ListDashboardProductBreakdownQuery:
    """Wire product drill-down query to the analytics repository."""

    repository = SqlAlchemyAnalyticsRepository(session)
    return ListDashboardProductBreakdownQuery(repository=repository)


def get_dashboard_product_source_rows_query(
    session: DbSession,
) -> ListDashboardProductSourceRowsQuery:
    """Wire product source-row drill-down query to the analytics repository."""

    repository = SqlAlchemyAnalyticsRepository(session)
    return ListDashboardProductSourceRowsQuery(repository=repository)


def get_dashboard_expense_details_query(
    session: DbSession,
) -> ListDashboardExpenseDetailsQuery:
    """Wire expense drill-down query to the analytics repository."""

    repository = SqlAlchemyAnalyticsRepository(session)
    return ListDashboardExpenseDetailsQuery(repository=repository)


def get_dashboard_expense_source_query(
    session: DbSession,
) -> GetDashboardExpenseSourceQuery:
    """Wire expense source drill-down query to the analytics repository."""

    repository = SqlAlchemyAnalyticsRepository(session)
    return GetDashboardExpenseSourceQuery(repository=repository)


def get_dashboard_basket_pairs_query(
    session: DbSession,
) -> ListDashboardBasketPairsQuery:
    """Wire basket pair query to the analytics repository."""

    repository = SqlAlchemyAnalyticsRepository(session)
    return ListDashboardBasketPairsQuery(repository=repository)


def get_dashboard_basket_pair_receipts_query(
    session: DbSession,
) -> ListDashboardBasketPairReceiptsQuery:
    """Wire basket pair source receipt query to the analytics repository."""

    repository = SqlAlchemyAnalyticsRepository(session)
    return ListDashboardBasketPairReceiptsQuery(repository=repository)
