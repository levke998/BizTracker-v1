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
    GetDashboardExpenseSourceQuery,
    GetDashboardDataQuery,
    ListDashboardBasketPairReceiptsQuery,
    ListDashboardBasketPairsQuery,
    ListDashboardCategoryBreakdownQuery,
    ListDashboardExpenseDetailsQuery,
    ListDashboardProductBreakdownQuery,
    ListDashboardProductSourceRowsQuery,
)
from app.modules.analytics.presentation.dependencies import (
    get_dashboard_basket_pairs_query,
    get_dashboard_basket_pair_receipts_query,
    get_dashboard_category_breakdown_query,
    get_dashboard_data_query,
    get_dashboard_expense_details_query,
    get_dashboard_expense_source_query,
    get_dashboard_product_breakdown_query,
    get_dashboard_product_source_rows_query,
)
from app.modules.analytics.presentation.schemas.dashboard import (
    DashboardBasketPairRowResponse,
    DashboardBasketReceiptResponse,
    DashboardBreakdownRowResponse,
    DashboardExpenseDetailRowResponse,
    DashboardExpenseSourceResponse,
    DashboardPosSourceRowResponse,
    DashboardProductDetailRowResponse,
    DashboardResponse,
)

router = APIRouter(prefix="/analytics", tags=["analytics"])

DashboardScope = Literal["overall", "flow", "gourmand"]
DashboardPeriodPreset = Literal[
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
    "/dashboard/product-rows",
    response_model=list[DashboardPosSourceRowResponse],
)
def list_dashboard_product_source_rows(
    query: Annotated[
        ListDashboardProductSourceRowsQuery,
        Depends(get_dashboard_product_source_rows_query),
    ],
    scope: DashboardScope = Query(default="overall"),
    period: DashboardPeriodPreset = Query(default="last_30_days"),
    business_unit_id: uuid.UUID | None = Query(default=None),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    product_name: str = Query(..., min_length=1),
    category_name: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[DashboardPosSourceRowResponse]:
    """Return POS source rows behind one dashboard product."""

    try:
        rows = query.execute(
            scope=scope,
            business_unit_id=business_unit_id,
            period=DashboardPeriodInput(
                preset=period,
                start_date=start_date,
                end_date=end_date,
            ),
            product_name=product_name,
            category_name=category_name,
            limit=limit,
        )
    except (DashboardScopeError, DashboardPeriodError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc

    return [DashboardPosSourceRowResponse.model_validate(row) for row in rows]


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


@router.get(
    "/dashboard/expense-source",
    response_model=DashboardExpenseSourceResponse,
)
def get_dashboard_expense_source(
    query: Annotated[
        GetDashboardExpenseSourceQuery,
        Depends(get_dashboard_expense_source_query),
    ],
    transaction_id: uuid.UUID = Query(...),
) -> DashboardExpenseSourceResponse:
    """Return source detail behind one dashboard expense transaction."""

    source = query.execute(transaction_id=transaction_id)
    if source is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense transaction was not found.",
        )

    return DashboardExpenseSourceResponse.model_validate(source)


@router.get(
    "/dashboard/basket-pairs",
    response_model=list[DashboardBasketPairRowResponse],
)
def list_dashboard_basket_pairs(
    query: Annotated[
        ListDashboardBasketPairsQuery,
        Depends(get_dashboard_basket_pairs_query),
    ],
    scope: DashboardScope = Query(default="overall"),
    period: DashboardPeriodPreset = Query(default="last_30_days"),
    business_unit_id: uuid.UUID | None = Query(default=None),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
) -> list[DashboardBasketPairRowResponse]:
    """Return frequently co-purchased product pairs for the dashboard context."""

    try:
        rows = query.execute(
            scope=scope,
            business_unit_id=business_unit_id,
            period=DashboardPeriodInput(
                preset=period,
                start_date=start_date,
                end_date=end_date,
            ),
            limit=limit,
        )
    except (DashboardScopeError, DashboardPeriodError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc

    return [DashboardBasketPairRowResponse.model_validate(row) for row in rows]


@router.get(
    "/dashboard/basket-pair-receipts",
    response_model=list[DashboardBasketReceiptResponse],
)
def list_dashboard_basket_pair_receipts(
    query: Annotated[
        ListDashboardBasketPairReceiptsQuery,
        Depends(get_dashboard_basket_pair_receipts_query),
    ],
    scope: DashboardScope = Query(default="overall"),
    period: DashboardPeriodPreset = Query(default="last_30_days"),
    business_unit_id: uuid.UUID | None = Query(default=None),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    product_a: str = Query(..., min_length=1),
    product_b: str = Query(..., min_length=1),
    limit: int = Query(default=20, ge=1, le=100),
) -> list[DashboardBasketReceiptResponse]:
    """Return source receipt baskets that contain one product pair."""

    try:
        rows = query.execute(
            scope=scope,
            business_unit_id=business_unit_id,
            period=DashboardPeriodInput(
                preset=period,
                start_date=start_date,
                end_date=end_date,
            ),
            product_a=product_a,
            product_b=product_b,
            limit=limit,
        )
    except (DashboardScopeError, DashboardPeriodError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc

    return [DashboardBasketReceiptResponse.model_validate(row) for row in rows]
