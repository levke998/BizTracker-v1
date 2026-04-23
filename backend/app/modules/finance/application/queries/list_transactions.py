"""Finance transaction list query."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from app.modules.finance.domain.entities.transaction import FinancialTransaction
from app.modules.finance.domain.repositories.transaction_repository import (
    FinancialTransactionRepository,
)


@dataclass(slots=True)
class ListFinancialTransactionsQuery:
    """Return finance transactions with lightweight filters."""

    repository: FinancialTransactionRepository

    def execute(
        self,
        *,
        business_unit_id: uuid.UUID | None = None,
        transaction_type: str | None = None,
        source_type: str | None = None,
        limit: int = 50,
    ) -> list[FinancialTransaction]:
        return self.repository.list_many(
            business_unit_id=business_unit_id,
            transaction_type=transaction_type,
            source_type=source_type,
            limit=limit,
        )
