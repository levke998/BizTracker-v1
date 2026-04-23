"""Finance repository contract."""

from __future__ import annotations

import uuid
from typing import Protocol

from app.modules.finance.domain.entities.transaction import (
    FinancialTransaction,
    NewFinancialTransaction,
)


class FinancialTransactionRepository(Protocol):
    """Defines persistence operations for finance transactions."""

    def create_many(
        self,
        transactions: list[NewFinancialTransaction],
    ) -> list[FinancialTransaction]:
        """Persist multiple finance transactions."""

    def has_source_references(
        self,
        *,
        source_type: str,
        source_ids: list[uuid.UUID],
    ) -> bool:
        """Return whether any transaction already exists for the source references."""

    def list_many(
        self,
        *,
        business_unit_id: uuid.UUID | None = None,
        transaction_type: str | None = None,
        source_type: str | None = None,
        limit: int = 50,
    ) -> list[FinancialTransaction]:
        """List finance transactions with simple filters."""
