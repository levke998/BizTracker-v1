"""Read recent demo POS receipts from persisted import and finance rows."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.finance.infrastructure.orm.transaction_model import (
    FinancialTransactionModel,
)
from app.modules.imports.infrastructure.orm.import_batch_model import ImportBatchModel
from app.modules.imports.infrastructure.orm.import_row_model import ImportRowModel


@dataclass(frozen=True, slots=True)
class DemoPosReceiptHistoryLine:
    """One persisted line of a POS receipt."""

    product_id: uuid.UUID
    product_name: str
    category_name: str | None
    quantity: Decimal
    unit_price_gross: Decimal
    gross_amount: Decimal
    import_row_id: uuid.UUID
    transaction_id: uuid.UUID


@dataclass(frozen=True, slots=True)
class DemoPosReceiptHistoryItem:
    """One persisted POS receipt summary."""

    business_unit_id: uuid.UUID
    receipt_no: str
    payment_method: str
    occurred_at: datetime
    batch_id: uuid.UUID
    gross_total: Decimal
    transaction_count: int
    lines: tuple[DemoPosReceiptHistoryLine, ...]


class ListDemoPosReceiptsQuery:
    """Return persisted POS receipts from the normalized import pipeline."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def execute(
        self,
        *,
        business_unit_id: uuid.UUID,
        limit: int = 20,
    ) -> list[DemoPosReceiptHistoryItem]:
        rows = self._session.execute(
            select(
                ImportBatchModel.business_unit_id,
                ImportBatchModel.id.label("batch_id"),
                ImportRowModel.id.label("row_id"),
                ImportRowModel.normalized_payload,
                FinancialTransactionModel.id.label("transaction_id"),
                FinancialTransactionModel.amount,
                FinancialTransactionModel.occurred_at,
            )
            .join(ImportBatchModel, ImportRowModel.batch_id == ImportBatchModel.id)
            .join(
                FinancialTransactionModel,
                FinancialTransactionModel.source_id == ImportRowModel.id,
            )
            .where(ImportBatchModel.business_unit_id == business_unit_id)
            .where(ImportBatchModel.import_type == "pos_sales")
            .where(ImportRowModel.parse_status == "parsed")
            .where(FinancialTransactionModel.transaction_type == "pos_sale")
            .order_by(
                FinancialTransactionModel.occurred_at.desc(),
                ImportRowModel.created_at.desc(),
            )
            .limit(limit * 10)
        ).all()

        grouped: dict[tuple[uuid.UUID, str], list[Any]] = {}
        for row in rows:
            payload = row.normalized_payload or {}
            receipt_no = str(payload.get("receipt_no") or "")
            if not receipt_no:
                continue
            grouped.setdefault((row.batch_id, receipt_no), []).append(row)

        receipts: list[DemoPosReceiptHistoryItem] = []
        for (_batch_id, receipt_no), receipt_rows in grouped.items():
            first = receipt_rows[0]
            payload = first.normalized_payload or {}
            lines = tuple(self._to_line(row) for row in receipt_rows)
            receipts.append(
                DemoPosReceiptHistoryItem(
                    business_unit_id=first.business_unit_id,
                    receipt_no=receipt_no,
                    payment_method=str(payload.get("payment_method") or "unknown"),
                    occurred_at=first.occurred_at,
                    batch_id=first.batch_id,
                    gross_total=sum(
                        (line.gross_amount for line in lines),
                        Decimal("0"),
                    ).quantize(Decimal("0.01")),
                    transaction_count=len(lines),
                    lines=lines,
                )
            )

        receipts.sort(key=lambda receipt: receipt.occurred_at, reverse=True)
        return receipts[:limit]

    @staticmethod
    def _to_line(row: Any) -> DemoPosReceiptHistoryLine:
        payload = row.normalized_payload or {}
        return DemoPosReceiptHistoryLine(
            product_id=uuid.UUID(str(payload["product_id"])),
            product_name=str(payload.get("product_name") or "Unknown product"),
            category_name=payload.get("category_name"),
            quantity=Decimal(str(payload.get("quantity") or "0")),
            unit_price_gross=Decimal(str(payload.get("unit_price_gross") or "0")),
            gross_amount=Decimal(str(payload.get("gross_amount") or row.amount or "0")),
            import_row_id=row.row_id,
            transaction_id=row.transaction_id,
        )
