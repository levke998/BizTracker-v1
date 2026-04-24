"""SQLAlchemy analytics read-model repository."""

from __future__ import annotations

import uuid
from collections import defaultdict
from datetime import UTC, date, datetime, time
from decimal import Decimal, InvalidOperation
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.analytics.domain.entities.dashboard_snapshot import (
    DashboardBreakdownRow,
    DashboardExpenseDetailRow,
    DashboardExpenseRow,
    DashboardKpi,
    DashboardPeriod,
    DashboardProductDetailRow,
    DashboardSnapshot,
    DashboardTrendPoint,
)
from app.modules.finance.infrastructure.orm.transaction_model import (
    FinancialTransactionModel,
)
from app.modules.imports.infrastructure.orm.import_batch_model import ImportBatchModel
from app.modules.imports.infrastructure.orm.import_row_model import ImportRowModel
from app.modules.master_data.infrastructure.orm.business_unit_model import (
    BusinessUnitModel,
)

BUSINESS_SCOPE_CODES = {
    "flow": "flow",
    "gourmand": "gourmand",
}
UNKNOWN_CATEGORY = "Uncategorized"
UNKNOWN_PRODUCT = "Unknown product"


class SqlAlchemyAnalyticsRepository:
    """Build dashboard read models from operational actuals and import rows."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_business_dashboard(
        self,
        *,
        scope: str,
        business_unit_id: uuid.UUID | None,
        preset: str,
        start_date: date,
        end_date: date,
        grain: str,
    ) -> DashboardSnapshot:
        resolved_business_unit_id, business_unit_name = self._resolve_business_unit(
            scope=scope,
            business_unit_id=business_unit_id,
        )
        transactions = self._list_financial_transactions(
            business_unit_id=resolved_business_unit_id,
            start_date=start_date,
            end_date=end_date,
        )
        import_rows = self._list_pos_sales_rows(
            business_unit_id=resolved_business_unit_id,
        )

        revenue = self._sum_transactions(transactions, direction="inflow")
        cost = self._sum_transactions(transactions, direction="outflow")
        profit = revenue - cost
        transaction_count = len(transactions)

        return DashboardSnapshot(
            scope=scope,
            business_unit_id=resolved_business_unit_id,
            business_unit_name=business_unit_name,
            period=DashboardPeriod(
                preset=preset,
                start_date=start_date,
                end_date=end_date,
                grain=grain,
            ),
            kpis=(
                DashboardKpi("revenue", "Revenue", revenue, "HUF", "financial_actual"),
                DashboardKpi("cost", "Cost", cost, "HUF", "financial_actual"),
                DashboardKpi("profit", "Profit", profit, "HUF", "derived_actual"),
                DashboardKpi(
                    "transaction_count",
                    "Transactions",
                    Decimal(transaction_count),
                    "count",
                    "financial_actual",
                ),
            ),
            revenue_trend=tuple(
                self._build_trend(
                    transactions=transactions,
                    start_date=start_date,
                    end_date=end_date,
                    grain=grain,
                )
            ),
            category_breakdown=tuple(
                self._build_pos_breakdown(
                    rows=import_rows,
                    start_date=start_date,
                    end_date=end_date,
                    key_name="category_name",
                    fallback=UNKNOWN_CATEGORY,
                    limit=12,
                )
            ),
            top_products=tuple(
                self._build_pos_breakdown(
                    rows=import_rows,
                    start_date=start_date,
                    end_date=end_date,
                    key_name="product_name",
                    fallback=UNKNOWN_PRODUCT,
                    limit=10,
                )
            ),
            expense_breakdown=tuple(
                self._build_expense_breakdown(transactions=transactions, limit=10)
            ),
            notes=(
                "Financial KPIs are calculated from core.financial_transaction actuals.",
                "Product and category breakdowns are derived from parsed pos_sales import rows.",
                "Profit currently uses revenue minus posted financial outflows; estimated COGS is not included yet.",
            ),
        )

    def list_category_breakdown(
        self,
        *,
        scope: str,
        business_unit_id: uuid.UUID | None,
        start_date: date,
        end_date: date,
    ) -> list[DashboardBreakdownRow]:
        resolved_business_unit_id, _business_unit_name = self._resolve_business_unit(
            scope=scope,
            business_unit_id=business_unit_id,
        )
        return self._build_pos_breakdown(
            rows=self._list_pos_sales_rows(business_unit_id=resolved_business_unit_id),
            start_date=start_date,
            end_date=end_date,
            key_name="category_name",
            fallback=UNKNOWN_CATEGORY,
            limit=200,
        )

    def list_product_breakdown(
        self,
        *,
        scope: str,
        business_unit_id: uuid.UUID | None,
        start_date: date,
        end_date: date,
        category_name: str | None = None,
    ) -> list[DashboardProductDetailRow]:
        resolved_business_unit_id, _business_unit_name = self._resolve_business_unit(
            scope=scope,
            business_unit_id=business_unit_id,
        )
        return self._build_product_detail_breakdown(
            rows=self._list_pos_sales_rows(business_unit_id=resolved_business_unit_id),
            start_date=start_date,
            end_date=end_date,
            category_name=category_name,
            limit=200,
        )

    def list_expense_details(
        self,
        *,
        scope: str,
        business_unit_id: uuid.UUID | None,
        start_date: date,
        end_date: date,
        transaction_type: str | None = None,
    ) -> list[DashboardExpenseDetailRow]:
        resolved_business_unit_id, _business_unit_name = self._resolve_business_unit(
            scope=scope,
            business_unit_id=business_unit_id,
        )
        transactions = self._list_financial_transactions(
            business_unit_id=resolved_business_unit_id,
            start_date=start_date,
            end_date=end_date,
        )
        expense_transactions = [
            transaction
            for transaction in transactions
            if transaction.direction == "outflow"
            and (
                transaction_type is None
                or transaction.transaction_type == transaction_type
            )
        ]
        return [
            DashboardExpenseDetailRow(
                transaction_id=transaction.id,
                transaction_type=transaction.transaction_type,
                amount=Decimal(transaction.amount),
                currency=transaction.currency,
                occurred_at=transaction.occurred_at.date(),
                description=transaction.description,
                source_type=transaction.source_type,
                source_id=transaction.source_id,
                source_layer="financial_actual",
            )
            for transaction in sorted(
                expense_transactions,
                key=lambda item: item.occurred_at,
                reverse=True,
            )[:200]
        ]

    def _resolve_business_unit(
        self,
        *,
        scope: str,
        business_unit_id: uuid.UUID | None,
    ) -> tuple[uuid.UUID | None, str | None]:
        if business_unit_id is not None:
            model = self._session.get(BusinessUnitModel, business_unit_id)
            return business_unit_id, model.name if model else None

        business_unit_code = BUSINESS_SCOPE_CODES.get(scope)
        if business_unit_code is None:
            return None, None

        model = self._session.scalar(
            select(BusinessUnitModel).where(BusinessUnitModel.code == business_unit_code)
        )
        if model is None:
            return None, None

        return model.id, model.name

    def _list_financial_transactions(
        self,
        *,
        business_unit_id: uuid.UUID | None,
        start_date: date,
        end_date: date,
    ) -> list[FinancialTransactionModel]:
        start_at = datetime.combine(start_date, time.min, tzinfo=UTC)
        end_at = datetime.combine(end_date, time.max, tzinfo=UTC)
        statement = select(FinancialTransactionModel).where(
            FinancialTransactionModel.occurred_at >= start_at,
            FinancialTransactionModel.occurred_at <= end_at,
        )

        if business_unit_id is not None:
            statement = statement.where(
                FinancialTransactionModel.business_unit_id == business_unit_id
            )

        return list(self._session.scalars(statement).all())

    def _list_pos_sales_rows(
        self,
        *,
        business_unit_id: uuid.UUID | None,
    ) -> list[ImportRowModel]:
        statement = (
            select(ImportRowModel)
            .join(ImportBatchModel, ImportBatchModel.id == ImportRowModel.batch_id)
            .where(ImportBatchModel.import_type == "pos_sales")
            .where(ImportRowModel.parse_status == "parsed")
        )

        if business_unit_id is not None:
            statement = statement.where(ImportBatchModel.business_unit_id == business_unit_id)

        return list(self._session.scalars(statement).all())

    @staticmethod
    def _sum_transactions(
        transactions: list[FinancialTransactionModel],
        *,
        direction: str,
    ) -> Decimal:
        return sum(
            (
                Decimal(transaction.amount)
                for transaction in transactions
                if transaction.direction == direction
            ),
            Decimal("0"),
        )

    def _build_trend(
        self,
        *,
        transactions: list[FinancialTransactionModel],
        start_date: date,
        end_date: date,
        grain: str,
    ) -> list[DashboardTrendPoint]:
        buckets = {
            bucket: {"revenue": Decimal("0"), "cost": Decimal("0")}
            for bucket in self._iter_buckets(start_date=start_date, end_date=end_date, grain=grain)
        }

        for transaction in transactions:
            bucket = self._bucket_date(transaction.occurred_at.date(), grain=grain)
            if bucket not in buckets:
                continue

            if transaction.direction == "inflow":
                buckets[bucket]["revenue"] += Decimal(transaction.amount)
            elif transaction.direction == "outflow":
                buckets[bucket]["cost"] += Decimal(transaction.amount)

        return [
            DashboardTrendPoint(
                period_start=bucket,
                revenue=values["revenue"],
                cost=values["cost"],
                profit=values["revenue"] - values["cost"],
            )
            for bucket, values in buckets.items()
        ]

    def _build_pos_breakdown(
        self,
        *,
        rows: list[ImportRowModel],
        start_date: date,
        end_date: date,
        key_name: str,
        fallback: str,
        limit: int,
    ) -> list[DashboardBreakdownRow]:
        aggregate: dict[str, dict[str, Decimal | int]] = defaultdict(
            lambda: {"revenue": Decimal("0"), "quantity": Decimal("0"), "count": 0}
        )

        for row in rows:
            payload = row.normalized_payload or {}
            row_date = self._parse_payload_date(payload.get("date"))
            if row_date is None or row_date < start_date or row_date > end_date:
                continue

            label = self._extract_text(payload.get(key_name), fallback=fallback)
            aggregate[label]["revenue"] += self._parse_decimal(payload.get("gross_amount"))
            aggregate[label]["quantity"] += self._parse_decimal(payload.get("quantity"))
            aggregate[label]["count"] += 1

        sorted_rows = sorted(
            aggregate.items(),
            key=lambda item: Decimal(item[1]["revenue"]),
            reverse=True,
        )
        return [
            DashboardBreakdownRow(
                label=label,
                revenue=Decimal(values["revenue"]),
                quantity=Decimal(values["quantity"]),
                transaction_count=int(values["count"]),
                source_layer="import_derived",
            )
            for label, values in sorted_rows[:limit]
        ]

    def _build_product_detail_breakdown(
        self,
        *,
        rows: list[ImportRowModel],
        start_date: date,
        end_date: date,
        category_name: str | None,
        limit: int,
    ) -> list[DashboardProductDetailRow]:
        aggregate: dict[tuple[str, str], dict[str, Decimal | int]] = defaultdict(
            lambda: {"revenue": Decimal("0"), "quantity": Decimal("0"), "count": 0}
        )

        for row in rows:
            payload = row.normalized_payload or {}
            row_date = self._parse_payload_date(payload.get("date"))
            if row_date is None or row_date < start_date or row_date > end_date:
                continue

            category = self._extract_text(
                payload.get("category_name"),
                fallback=UNKNOWN_CATEGORY,
            )
            if category_name is not None and category != category_name:
                continue

            product = self._extract_text(
                payload.get("product_name"),
                fallback=UNKNOWN_PRODUCT,
            )
            key = (product, category)
            aggregate[key]["revenue"] += self._parse_decimal(payload.get("gross_amount"))
            aggregate[key]["quantity"] += self._parse_decimal(payload.get("quantity"))
            aggregate[key]["count"] += 1

        sorted_rows = sorted(
            aggregate.items(),
            key=lambda item: Decimal(item[1]["revenue"]),
            reverse=True,
        )
        return [
            DashboardProductDetailRow(
                product_name=product,
                category_name=category,
                revenue=Decimal(values["revenue"]),
                quantity=Decimal(values["quantity"]),
                transaction_count=int(values["count"]),
                source_layer="import_derived",
            )
            for (product, category), values in sorted_rows[:limit]
        ]

    @staticmethod
    def _build_expense_breakdown(
        *,
        transactions: list[FinancialTransactionModel],
        limit: int,
    ) -> list[DashboardExpenseRow]:
        aggregate: dict[str, dict[str, Decimal | int]] = defaultdict(
            lambda: {"amount": Decimal("0"), "count": 0}
        )

        for transaction in transactions:
            if transaction.direction != "outflow":
                continue

            label = transaction.transaction_type or "expense"
            aggregate[label]["amount"] += Decimal(transaction.amount)
            aggregate[label]["count"] += 1

        sorted_rows = sorted(
            aggregate.items(),
            key=lambda item: Decimal(item[1]["amount"]),
            reverse=True,
        )
        return [
            DashboardExpenseRow(
                label=label,
                amount=Decimal(values["amount"]),
                transaction_count=int(values["count"]),
                source_layer="financial_actual",
            )
            for label, values in sorted_rows[:limit]
        ]

    @staticmethod
    def _iter_buckets(
        *,
        start_date: date,
        end_date: date,
        grain: str,
    ) -> list[date]:
        buckets: list[date] = []
        current = start_date.replace(day=1) if grain == "month" else start_date
        while current <= end_date:
            buckets.append(current)
            if grain == "month":
                current = (
                    current.replace(year=current.year + 1, month=1)
                    if current.month == 12
                    else current.replace(month=current.month + 1)
                )
            else:
                current = current.fromordinal(current.toordinal() + 1)
        return buckets

    @staticmethod
    def _bucket_date(value: date, *, grain: str) -> date:
        if grain == "month":
            return value.replace(day=1)
        return value

    @staticmethod
    def _parse_payload_date(value: Any) -> date | None:
        if not isinstance(value, str):
            return None
        try:
            return date.fromisoformat(value)
        except ValueError:
            return None

    @staticmethod
    def _parse_decimal(value: Any) -> Decimal:
        if value is None:
            return Decimal("0")
        try:
            return Decimal(str(value))
        except (InvalidOperation, ValueError):
            return Decimal("0")

    @staticmethod
    def _extract_text(value: Any, *, fallback: str) -> str:
        if isinstance(value, str) and value.strip():
            return value.strip()
        return fallback
