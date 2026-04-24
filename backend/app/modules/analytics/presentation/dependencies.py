"""Analytics presentation dependency wiring."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.modules.analytics.application.queries.get_dashboard_data import (
    GetDashboardDataQuery,
    ListDashboardCategoryBreakdownQuery,
    ListDashboardExpenseDetailsQuery,
    ListDashboardProductBreakdownQuery,
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


def get_dashboard_expense_details_query(
    session: DbSession,
) -> ListDashboardExpenseDetailsQuery:
    """Wire expense drill-down query to the analytics repository."""

    repository = SqlAlchemyAnalyticsRepository(session)
    return ListDashboardExpenseDetailsQuery(repository=repository)
