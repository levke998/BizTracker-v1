"""Analytics API routes."""

from __future__ import annotations

import uuid
from datetime import date
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.modules.analytics.application.queries.get_dashboard_data import (
    DashboardPeriodError,
    DashboardPeriodInput,
    DashboardScopeError,
    GetDashboardDataQuery,
    ListDashboardCategoryBreakdownQuery,
    ListDashboardExpenseDetailsQuery,
    ListDashboardProductBreakdownQuery,
)
from app.modules.analytics.presentation.dependencies import (
    get_dashboard_category_breakdown_query,
    get_dashboard_data_query,
    get_dashboard_expense_details_query,
    get_dashboard_product_breakdown_query,
)
from app.modules.analytics.presentation.schemas.dashboard import (
    DashboardBreakdownRowResponse,
    DashboardExpenseDetailRowResponse,
    DashboardProductDetailRowResponse,
    DashboardResponse,
)

router = APIRouter(prefix="/analytics", tags=["analytics"])

DashboardScope = Literal["overall", "flow", "gourmand"]
DashboardPeriodPreset = Literal[
    "today",
    "week",
    "month",
    "year",
    "last_7_days",
    "last_30_days",
    "custom",
]


@router.get("/dashboard", response_model=DashboardResponse)
def get_dashboard(
    query: Annotated[GetDashboardDataQuery, Depends(get_dashboard_data_query)],
    scope: DashboardScope = Query(default="overall"),
    period: DashboardPeriodPreset = Query(default="last_30_days"),
    business_unit_id: uuid.UUID | None = Query(default=None),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
) -> DashboardResponse:
    """Return the first real business dashboard read model."""

    try:
        snapshot = query.execute(
            scope=scope,
            business_unit_id=business_unit_id,
            period=DashboardPeriodInput(
                preset=period,
                start_date=start_date,
                end_date=end_date,
            ),
        )
    except (DashboardScopeError, DashboardPeriodError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc

    return DashboardResponse.model_validate(snapshot)


@router.get(
    "/dashboard/categories",
    response_model=list[DashboardBreakdownRowResponse],
)
def list_dashboard_categories(
    query: Annotated[
        ListDashboardCategoryBreakdownQuery,
        Depends(get_dashboard_category_breakdown_query),
    ],
    scope: DashboardScope = Query(default="overall"),
    period: DashboardPeriodPreset = Query(default="last_30_days"),
    business_unit_id: uuid.UUID | None = Query(default=None),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
) -> list[DashboardBreakdownRowResponse]:
    """Return category drill-down rows for the dashboard context."""

    try:
        rows = query.execute(
            scope=scope,
            business_unit_id=business_unit_id,
            period=DashboardPeriodInput(
                preset=period,
                start_date=start_date,
                end_date=end_date,
            ),
        )
    except (DashboardScopeError, DashboardPeriodError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc

    return [DashboardBreakdownRowResponse.model_validate(row) for row in rows]


@router.get(
    "/dashboard/products",
    response_model=list[DashboardProductDetailRowResponse],
)
def list_dashboard_products(
    query: Annotated[
        ListDashboardProductBreakdownQuery,
        Depends(get_dashboard_product_breakdown_query),
    ],
    scope: DashboardScope = Query(default="overall"),
    period: DashboardPeriodPreset = Query(default="last_30_days"),
    business_unit_id: uuid.UUID | None = Query(default=None),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    category_name: str | None = Query(default=None),
) -> list[DashboardProductDetailRowResponse]:
    """Return product drill-down rows for the dashboard context."""

    try:
        rows = query.execute(
            scope=scope,
            business_unit_id=business_unit_id,
            period=DashboardPeriodInput(
                preset=period,
                start_date=start_date,
                end_date=end_date,
            ),
            category_name=category_name,
        )
    except (DashboardScopeError, DashboardPeriodError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc

    return [DashboardProductDetailRowResponse.model_validate(row) for row in rows]


@router.get(
    "/dashboard/expenses",
    response_model=list[DashboardExpenseDetailRowResponse],
)
def list_dashboard_expenses(
    query: Annotated[
        ListDashboardExpenseDetailsQuery,
        Depends(get_dashboard_expense_details_query),
    ],
    scope: DashboardScope = Query(default="overall"),
    period: DashboardPeriodPreset = Query(default="last_30_days"),
    business_unit_id: uuid.UUID | None = Query(default=None),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    transaction_type: str | None = Query(default=None),
) -> list[DashboardExpenseDetailRowResponse]:
    """Return expense transaction rows for the dashboard context."""

    try:
        rows = query.execute(
            scope=scope,
            business_unit_id=business_unit_id,
            period=DashboardPeriodInput(
                preset=period,
                start_date=start_date,
                end_date=end_date,
            ),
            transaction_type=transaction_type,
        )
    except (DashboardScopeError, DashboardPeriodError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc

    return [DashboardExpenseDetailRowResponse.model_validate(row) for row in rows]
