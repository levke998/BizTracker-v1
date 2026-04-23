"""Finance read API routes."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.modules.finance.application.queries.list_transactions import (
    ListFinancialTransactionsQuery,
)
from app.modules.finance.presentation.dependencies import (
    get_list_financial_transactions_query,
)
from app.modules.finance.presentation.schemas.transaction import (
    FinancialTransactionResponse,
)

router = APIRouter(prefix="/finance", tags=["finance"])


@router.get("/transactions", response_model=list[FinancialTransactionResponse])
def list_financial_transactions(
    query: Annotated[
        ListFinancialTransactionsQuery,
        Depends(get_list_financial_transactions_query),
    ],
    business_unit_id: uuid.UUID | None = Query(default=None),
    transaction_type: str | None = Query(default=None),
    source_type: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[FinancialTransactionResponse]:
    """Return finance transactions with minimal filters."""

    items = query.execute(
        business_unit_id=business_unit_id,
        transaction_type=transaction_type,
        source_type=source_type,
        limit=limit,
    )
    return [FinancialTransactionResponse.model_validate(item) for item in items]
