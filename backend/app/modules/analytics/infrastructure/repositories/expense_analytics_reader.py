"""Expense analytics read-model queries and mapping."""

from __future__ import annotations

import uuid
from collections import defaultdict
from decimal import Decimal

import sqlalchemy as sa
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.analytics.domain.entities.dashboard_snapshot import (
    DashboardExpenseDetailRow,
    DashboardExpenseRow,
    DashboardExpenseSource,
    DashboardExpenseSourceLine,
)
from app.modules.finance.infrastructure.orm.transaction_model import (
    FinancialTransactionModel,
)
from app.modules.procurement.infrastructure.orm.purchase_invoice_line_model import (
    PurchaseInvoiceLineModel,
)
from app.modules.procurement.infrastructure.orm.purchase_invoice_model import (
    PurchaseInvoiceModel,
)
from app.modules.procurement.infrastructure.orm.supplier_model import SupplierModel

SUPPLIER_INVOICE_SOURCE_TYPE = "supplier_invoice"


class ExpenseAnalyticsReader:
    """Read and map expense analytics, including supplier invoice sources."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def build_breakdown(
        self,
        *,
        transactions: list[FinancialTransactionModel],
        limit: int,
    ) -> list[DashboardExpenseRow]:
        expense_transactions = [
            transaction
            for transaction in transactions
            if transaction.direction == "outflow"
        ]
        tax_totals = self._load_supplier_invoice_tax_totals(expense_transactions)
        aggregate: dict[str, dict[str, Decimal | int]] = defaultdict(
            lambda: {
                "amount": Decimal("0"),
                "net_amount": Decimal("0"),
                "vat_amount": Decimal("0"),
                "tax_count": 0,
                "count": 0,
            }
        )

        for transaction in expense_transactions:
            label = transaction.transaction_type or "expense"
            aggregate[label]["amount"] += Decimal(transaction.amount)
            aggregate[label]["count"] += 1
            tax_total = tax_totals.get(transaction.source_id)
            if tax_total is not None:
                aggregate[label]["net_amount"] += tax_total["net_amount"]
                aggregate[label]["vat_amount"] += tax_total["vat_amount"]
                aggregate[label]["tax_count"] += 1

        sorted_rows = sorted(
            aggregate.items(),
            key=lambda item: Decimal(item[1]["amount"]),
            reverse=True,
        )
        return [
            self._build_breakdown_row(label=label, values=values)
            for label, values in sorted_rows[:limit]
        ]

    def list_details(
        self,
        *,
        transactions: list[FinancialTransactionModel],
        transaction_type: str | None,
        limit: int = 200,
    ) -> list[DashboardExpenseDetailRow]:
        expense_transactions = [
            transaction
            for transaction in transactions
            if transaction.direction == "outflow"
            and (
                transaction_type is None
                or transaction.transaction_type == transaction_type
            )
        ]
        tax_totals = self._load_supplier_invoice_tax_totals(expense_transactions)
        return [
            DashboardExpenseDetailRow(
                transaction_id=transaction.id,
                transaction_type=transaction.transaction_type,
                amount=Decimal(transaction.amount),
                gross_amount=Decimal(transaction.amount),
                net_amount=tax_totals.get(transaction.source_id, {}).get("net_amount"),
                vat_amount=tax_totals.get(transaction.source_id, {}).get("vat_amount"),
                currency=transaction.currency,
                occurred_at=transaction.occurred_at.date(),
                description=transaction.description,
                source_type=transaction.source_type,
                source_id=transaction.source_id,
                source_layer="financial_actual",
                amount_basis="gross",
                tax_breakdown_source=(
                    "supplier_invoice_actual"
                    if transaction.source_id in tax_totals
                    else "not_available"
                ),
            )
            for transaction in sorted(
                expense_transactions,
                key=lambda item: item.occurred_at,
                reverse=True,
            )[:limit]
        ]

    def get_source(
        self,
        *,
        transaction_id: uuid.UUID,
    ) -> DashboardExpenseSource | None:
        transaction = self._session.get(FinancialTransactionModel, transaction_id)
        if transaction is None:
            return None

        if transaction.source_type != SUPPLIER_INVOICE_SOURCE_TYPE:
            return self._build_unresolved_source(transaction)

        invoice_row = self._session.execute(
            select(PurchaseInvoiceModel, SupplierModel.name)
            .join(SupplierModel, SupplierModel.id == PurchaseInvoiceModel.supplier_id)
            .where(PurchaseInvoiceModel.id == transaction.source_id)
        ).one_or_none()
        if invoice_row is None:
            return self._build_unresolved_source(transaction)

        invoice, supplier_name = invoice_row
        lines = self._session.scalars(
            select(PurchaseInvoiceLineModel)
            .where(PurchaseInvoiceLineModel.invoice_id == invoice.id)
            .order_by(PurchaseInvoiceLineModel.description.asc())
        ).all()
        net_total = sum((Decimal(line.line_net_amount) for line in lines), Decimal("0"))
        vat_total = sum(
            (
                Decimal(line.vat_amount)
                for line in lines
                if line.vat_amount is not None
            ),
            Decimal("0"),
        )

        return DashboardExpenseSource(
            transaction_id=transaction.id,
            transaction_type=transaction.transaction_type,
            amount=Decimal(transaction.amount),
            gross_amount=Decimal(invoice.gross_total),
            net_amount=net_total,
            vat_amount=vat_total,
            currency=transaction.currency,
            occurred_at=transaction.occurred_at.date(),
            source_type=transaction.source_type,
            source_id=transaction.source_id,
            supplier_id=invoice.supplier_id,
            supplier_name=supplier_name,
            invoice_number=invoice.invoice_number,
            invoice_date=invoice.invoice_date,
            gross_total=Decimal(invoice.gross_total),
            net_total=net_total,
            vat_total=vat_total,
            notes=invoice.notes,
            amount_basis="gross",
            tax_breakdown_source="supplier_invoice_actual",
            lines=tuple(self._build_source_line(line) for line in lines),
        )

    def _load_supplier_invoice_tax_totals(
        self,
        transactions: list[FinancialTransactionModel],
    ) -> dict[uuid.UUID, dict[str, Decimal]]:
        invoice_ids = [
            transaction.source_id
            for transaction in transactions
            if transaction.source_type == SUPPLIER_INVOICE_SOURCE_TYPE
        ]
        if not invoice_ids:
            return {}

        rows = self._session.execute(
            select(
                PurchaseInvoiceLineModel.invoice_id,
                sa.func.coalesce(
                    sa.func.sum(PurchaseInvoiceLineModel.line_net_amount),
                    0,
                ),
                sa.func.coalesce(
                    sa.func.sum(PurchaseInvoiceLineModel.vat_amount),
                    0,
                ),
            )
            .where(PurchaseInvoiceLineModel.invoice_id.in_(invoice_ids))
            .group_by(PurchaseInvoiceLineModel.invoice_id)
        ).all()
        return {
            invoice_id: {
                "net_amount": Decimal(net_amount),
                "vat_amount": Decimal(vat_amount),
            }
            for invoice_id, net_amount, vat_amount in rows
        }

    @staticmethod
    def _build_breakdown_row(
        *,
        label: str,
        values: dict[str, Decimal | int],
    ) -> DashboardExpenseRow:
        tax_count = int(values["tax_count"])
        transaction_count = int(values["count"])
        return DashboardExpenseRow(
            label=label,
            amount=Decimal(values["amount"]),
            gross_amount=Decimal(values["amount"]),
            net_amount=(
                Decimal(values["net_amount"]) if tax_count > 0 else None
            ),
            vat_amount=(
                Decimal(values["vat_amount"]) if tax_count > 0 else None
            ),
            transaction_count=transaction_count,
            source_layer="financial_actual",
            amount_basis="gross",
            tax_breakdown_source=(
                "supplier_invoice_actual"
                if tax_count == transaction_count
                else (
                    "partial_supplier_invoice_actual"
                    if tax_count > 0
                    else "not_available"
                )
            ),
        )

    @staticmethod
    def _build_unresolved_source(
        transaction: FinancialTransactionModel,
    ) -> DashboardExpenseSource:
        return DashboardExpenseSource(
            transaction_id=transaction.id,
            transaction_type=transaction.transaction_type,
            amount=Decimal(transaction.amount),
            gross_amount=Decimal(transaction.amount),
            net_amount=None,
            vat_amount=None,
            currency=transaction.currency,
            occurred_at=transaction.occurred_at.date(),
            source_type=transaction.source_type,
            source_id=transaction.source_id,
            supplier_id=None,
            supplier_name=None,
            invoice_number=None,
            invoice_date=None,
            gross_total=None,
            net_total=None,
            vat_total=None,
            notes=None,
            amount_basis="gross",
            tax_breakdown_source="not_available",
            lines=(),
        )

    @staticmethod
    def _build_source_line(
        line: PurchaseInvoiceLineModel,
    ) -> DashboardExpenseSourceLine:
        return DashboardExpenseSourceLine(
            line_id=line.id,
            inventory_item_id=line.inventory_item_id,
            description=line.description,
            quantity=Decimal(line.quantity),
            uom_id=line.uom_id,
            unit_net_amount=Decimal(line.unit_net_amount),
            line_net_amount=Decimal(line.line_net_amount),
            vat_rate_id=line.vat_rate_id,
            vat_amount=(
                Decimal(line.vat_amount) if line.vat_amount is not None else None
            ),
            line_gross_amount=(
                Decimal(line.line_gross_amount)
                if line.line_gross_amount is not None
                else None
            ),
        )
