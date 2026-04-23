"""Finance presentation dependency wiring."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.modules.finance.application.queries.list_transactions import (
    ListFinancialTransactionsQuery,
)
from app.modules.finance.infrastructure.repositories.sqlalchemy_transaction_repository import (
    SqlAlchemyFinancialTransactionRepository,
)

DbSession = Annotated[Session, Depends(get_db_session)]


def get_list_financial_transactions_query(
    session: DbSession,
) -> ListFinancialTransactionsQuery:
    """Wire the finance transaction list query to its repository."""

    repository = SqlAlchemyFinancialTransactionRepository(session)
    return ListFinancialTransactionsQuery(repository=repository)
