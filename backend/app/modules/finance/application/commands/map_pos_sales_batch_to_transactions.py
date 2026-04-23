"""Map parsed pos_sales import rows into finance transactions."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, date, datetime, time
from decimal import Decimal, InvalidOperation
from typing import Mapping, Any

from app.modules.finance.domain.entities.transaction import NewFinancialTransaction
from app.modules.finance.domain.repositories.transaction_repository import (
    FinancialTransactionRepository,
)
from app.modules.imports.domain.entities.import_batch import ImportBatch, ImportRow
from app.modules.imports.domain.repositories.import_batch_repository import (
    ImportBatchRepository,
)


class ImportBatchNotFoundError(Exception):
    """Raised when the requested import batch does not exist."""


class ImportBatchMappingStateError(Exception):
    """Raised when the batch cannot be mapped in its current state."""


class ImportBatchMappingValueError(Exception):
    """Raised when a parsed row cannot be mapped into a finance transaction."""


@dataclass(frozen=True, slots=True)
class FinancialTransactionMappingResult:
    """Small summary returned after a successful mapping run."""

    batch_id: uuid.UUID
    created_transactions: int
    transaction_type: str
    source_type: str


class MapPosSalesBatchToTransactionsCommand:
    """Create finance transactions from a parsed pos_sales import batch."""

    source_type = "import_row"
    direction = "inflow"
    transaction_type = "pos_sale"
    currency = "HUF"

    def __init__(
        self,
        imports_repository: ImportBatchRepository,
        finance_repository: FinancialTransactionRepository,
    ) -> None:
        self._imports_repository = imports_repository
        self._finance_repository = finance_repository

    def execute(self, *, batch_id: uuid.UUID) -> FinancialTransactionMappingResult:
        batch = self._imports_repository.get_batch(batch_id)
        if batch is None:
            raise ImportBatchNotFoundError(f"Import batch {batch_id} was not found.")

        if batch.status != "parsed":
            raise ImportBatchMappingStateError(
                "Only parsed batches can be mapped to financial transactions."
            )

        if batch.import_type != "pos_sales":
            raise ImportBatchMappingStateError(
                f"Only pos_sales batches are supported. Current type: {batch.import_type}."
            )

        parsed_rows = [row for row in batch.rows if row.parse_status == "parsed"]
        if not parsed_rows:
            raise ImportBatchMappingStateError(
                "The parsed batch does not contain any parsed rows to map."
            )

        source_ids = [row.id for row in parsed_rows]
        if self._finance_repository.has_source_references(
            source_type=self.source_type,
            source_ids=source_ids,
        ):
            raise ImportBatchMappingStateError(
                "This batch has already been mapped to financial transactions."
            )

        transactions = [
            self._map_row(batch=batch, row=row)
            for row in parsed_rows
        ]
        created = self._finance_repository.create_many(transactions)

        return FinancialTransactionMappingResult(
            batch_id=batch.id,
            created_transactions=len(created),
            transaction_type=self.transaction_type,
            source_type=self.source_type,
        )

    def _map_row(
        self,
        *,
        batch: ImportBatch,
        row: ImportRow,
    ) -> NewFinancialTransaction:
        payload = row.normalized_payload or {}

        amount = self._extract_amount(payload)
        occurred_at = self._extract_occurred_at(payload)
        description = self._build_description(payload)

        return NewFinancialTransaction(
            business_unit_id=batch.business_unit_id,
            direction=self.direction,
            transaction_type=self.transaction_type,
            amount=amount,
            currency=self.currency,
            occurred_at=occurred_at,
            description=description,
            source_type=self.source_type,
            source_id=row.id,
        )

    @staticmethod
    def _extract_amount(payload: Mapping[str, Any]) -> Decimal:
        value = payload.get("gross_amount")
        if value is None:
            raise ImportBatchMappingValueError(
                "The parsed row does not contain a usable gross_amount value."
            )

        try:
            return Decimal(str(value))
        except (InvalidOperation, ValueError) as exc:
            raise ImportBatchMappingValueError(
                f"Invalid gross_amount value for finance mapping: {value!r}."
            ) from exc

    @staticmethod
    def _extract_occurred_at(payload: Mapping[str, Any]) -> datetime:
        value = payload.get("date")
        if not isinstance(value, str) or not value:
            raise ImportBatchMappingValueError(
                "The parsed row does not contain a usable date value."
            )

        try:
            parsed_date = date.fromisoformat(value)
        except ValueError as exc:
            raise ImportBatchMappingValueError(
                f"Invalid date value for finance mapping: {value!r}."
            ) from exc

        return datetime.combine(parsed_date, time.min, tzinfo=UTC)

    @staticmethod
    def _build_description(payload: Mapping[str, Any]) -> str:
        product_name = payload.get("product_name")
        receipt_no = payload.get("receipt_no")

        if isinstance(product_name, str) and isinstance(receipt_no, str):
            return f"{product_name} ({receipt_no})"
        if isinstance(product_name, str):
            return product_name
        if isinstance(receipt_no, str):
            return f"Receipt {receipt_no}"

        return "POS sale import"
