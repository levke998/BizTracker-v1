"""Unit tests for the expense analytics infrastructure reader."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace

from app.modules.analytics.infrastructure.repositories.expense_analytics_reader import (
    ExpenseAnalyticsReader,
)


class _ExecuteResult:
    def __init__(self, rows: list[tuple[object, ...]]) -> None:
        self._rows = rows

    def all(self) -> list[tuple[object, ...]]:
        return self._rows


class _SessionStub:
    def __init__(
        self,
        *,
        tax_rows: list[tuple[object, ...]] | None = None,
        transaction: SimpleNamespace | None = None,
    ) -> None:
        self._tax_rows = tax_rows or []
        self._transaction = transaction

    def execute(self, _statement: object) -> _ExecuteResult:
        return _ExecuteResult(self._tax_rows)

    def get(self, _model: object, _identifier: uuid.UUID) -> SimpleNamespace | None:
        return self._transaction


def _transaction(
    *,
    amount: str,
    transaction_type: str,
    source_type: str,
    source_id: uuid.UUID | None = None,
    direction: str = "outflow",
    hour: int = 10,
) -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid.uuid4(),
        direction=direction,
        transaction_type=transaction_type,
        amount=Decimal(amount),
        currency="HUF",
        occurred_at=datetime(2026, 6, 10, hour, tzinfo=UTC),
        description=f"{transaction_type} expense",
        source_type=source_type,
        source_id=source_id or uuid.uuid4(),
    )


def test_breakdown_marks_partial_supplier_invoice_tax_coverage() -> None:
    invoice_id = uuid.uuid4()
    reader = ExpenseAnalyticsReader(
        _SessionStub(
            tax_rows=[(invoice_id, Decimal("1000"), Decimal("270"))],
        )
    )

    result = reader.build_breakdown(
        transactions=[
            _transaction(
                amount="1270",
                transaction_type="supplier_invoice",
                source_type="supplier_invoice",
                source_id=invoice_id,
            ),
            _transaction(
                amount="500",
                transaction_type="supplier_invoice",
                source_type="manual_expense",
            ),
        ],
        limit=10,
    )

    assert len(result) == 1
    assert result[0].gross_amount == Decimal("1770")
    assert result[0].net_amount == Decimal("1000")
    assert result[0].vat_amount == Decimal("270")
    assert result[0].transaction_count == 2
    assert result[0].tax_breakdown_source == "partial_supplier_invoice_actual"


def test_details_filter_out_inflows_and_other_transaction_types() -> None:
    reader = ExpenseAnalyticsReader(_SessionStub())
    kept = _transaction(
        amount="500",
        transaction_type="rent",
        source_type="manual_expense",
        hour=12,
    )

    result = reader.list_details(
        transactions=[
            _transaction(
                amount="100",
                transaction_type="utilities",
                source_type="manual_expense",
            ),
            kept,
            _transaction(
                amount="900",
                transaction_type="rent",
                source_type="bank",
                direction="inflow",
            ),
        ],
        transaction_type="rent",
    )

    assert len(result) == 1
    assert result[0].transaction_id == kept.id
    assert result[0].gross_amount == Decimal("500")
    assert result[0].tax_breakdown_source == "not_available"


def test_non_invoice_source_returns_traceable_unresolved_read_model() -> None:
    transaction = _transaction(
        amount="850",
        transaction_type="rent",
        source_type="manual_expense",
    )
    reader = ExpenseAnalyticsReader(_SessionStub(transaction=transaction))

    result = reader.get_source(transaction_id=transaction.id)

    assert result is not None
    assert result.transaction_id == transaction.id
    assert result.gross_amount == Decimal("850")
    assert result.supplier_id is None
    assert result.lines == ()
    assert result.tax_breakdown_source == "not_available"
