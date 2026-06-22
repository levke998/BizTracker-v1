"""Build POS sales analytics read models from already loaded persistence rows."""

from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from itertools import combinations
from typing import Any
from zoneinfo import ZoneInfo

from app.modules.analytics.domain.entities.dashboard_snapshot import (
    DashboardBasketPairRow,
    DashboardBasketReceipt,
    DashboardBasketReceiptLine,
    DashboardBreakdownRow,
    DashboardPosSourceRow,
    DashboardProductDetailRow,
    DashboardTrendPoint,
)
from app.modules.analytics.infrastructure.repositories.pos_financial_metrics import (
    calculate_payload_tax,
    cost_source,
    margin_status,
    tax_breakdown_source,
)
from app.modules.finance.infrastructure.orm.transaction_model import (
    FinancialTransactionModel,
)
from app.modules.imports.infrastructure.orm.import_row_model import ImportRowModel


class PosSalesAnalyticsBuilder:
    """Aggregate normalized POS rows without owning persistence concerns."""

    def __init__(
        self,
        *,
        time_zone: ZoneInfo,
        unknown_category: str,
        unknown_product: str,
    ) -> None:
        self._time_zone = time_zone
        self._unknown_category = unknown_category
        self._unknown_product = unknown_product

    def sum_estimated_cogs(
        self,
        *,
        rows: list[ImportRowModel],
        product_costs: dict[str, Decimal],
        start_at: datetime,
        end_at: datetime,
    ) -> Decimal:
        total = Decimal("0")
        for row in rows:
            payload = row.normalized_payload or {}
            if not self._is_in_period(payload, start_at=start_at, end_at=end_at):
                continue
            total += (
                self._lookup_unit_cost(payload, product_costs)
                * self._parse_decimal(payload.get("quantity"))
            )
        return total

    def build_trend(
        self,
        *,
        transactions: list[FinancialTransactionModel],
        rows: list[ImportRowModel],
        product_costs: dict[str, Decimal],
        start_at: datetime,
        end_at: datetime,
        grain: str,
    ) -> list[DashboardTrendPoint]:
        buckets = {
            bucket: {
                "revenue": Decimal("0"),
                "cost": Decimal("0"),
                "estimated_cogs": Decimal("0"),
            }
            for bucket in self._iter_buckets(
                start_at=start_at,
                end_at=end_at,
                grain=grain,
            )
        }

        for transaction in transactions:
            bucket = self._bucket_datetime(transaction.occurred_at, grain=grain)
            if bucket not in buckets:
                continue
            if transaction.direction == "inflow":
                buckets[bucket]["revenue"] += Decimal(transaction.amount)
            elif transaction.direction == "outflow":
                buckets[bucket]["cost"] += Decimal(transaction.amount)

        for row in rows:
            payload = row.normalized_payload or {}
            occurred_at = self._payload_occurred_at(payload)
            if occurred_at is None or occurred_at < start_at or occurred_at > end_at:
                continue
            bucket = self._bucket_datetime(occurred_at, grain=grain)
            if bucket not in buckets:
                continue
            buckets[bucket]["estimated_cogs"] += (
                self._lookup_unit_cost(payload, product_costs)
                * self._parse_decimal(payload.get("quantity"))
            )

        return [
            DashboardTrendPoint(
                period_start=bucket,
                revenue=values["revenue"],
                cost=values["cost"],
                profit=values["revenue"] - values["cost"],
                estimated_cogs=values["estimated_cogs"],
                margin_profit=values["revenue"] - values["estimated_cogs"],
            )
            for bucket, values in buckets.items()
        ]

    def build_breakdown(
        self,
        *,
        rows: list[ImportRowModel],
        start_at: datetime,
        end_at: datetime,
        key_name: str,
        fallback: str,
        limit: int,
        product_vat_rates: dict[str, Decimal] | None = None,
    ) -> list[DashboardBreakdownRow]:
        aggregate: dict[str, dict[str, Decimal | int]] = defaultdict(
            lambda: {
                "revenue": Decimal("0"),
                "net_revenue": Decimal("0"),
                "vat_amount": Decimal("0"),
                "quantity": Decimal("0"),
                "count": 0,
                "tax_count": 0,
            }
        )
        vat_rates = product_vat_rates or {}

        for row in rows:
            payload = row.normalized_payload or {}
            if not self._is_in_period(payload, start_at=start_at, end_at=end_at):
                continue

            label = self._extract_text(payload.get(key_name), fallback=fallback)
            gross_amount = self._parse_decimal(payload.get("gross_amount"))
            tax = calculate_payload_tax(
                payload=payload,
                gross_amount=gross_amount,
                product_vat_rates=vat_rates,
            )
            aggregate[label]["revenue"] += gross_amount
            aggregate[label]["quantity"] += self._parse_decimal(payload.get("quantity"))
            aggregate[label]["count"] += 1
            if tax.net_amount is not None and tax.vat_amount is not None:
                aggregate[label]["net_revenue"] += tax.net_amount
                aggregate[label]["vat_amount"] += tax.vat_amount
                aggregate[label]["tax_count"] += 1

        sorted_rows = sorted(
            aggregate.items(),
            key=lambda item: Decimal(item[1]["revenue"]),
            reverse=True,
        )
        return [
            DashboardBreakdownRow(
                label=label,
                revenue=Decimal(values["revenue"]),
                net_revenue=(
                    Decimal(values["net_revenue"])
                    if int(values["tax_count"]) > 0
                    else None
                ),
                vat_amount=(
                    Decimal(values["vat_amount"])
                    if int(values["tax_count"]) > 0
                    else None
                ),
                quantity=Decimal(values["quantity"]),
                transaction_count=int(values["count"]),
                source_layer="import_derived",
                amount_basis="gross",
                tax_breakdown_source=tax_breakdown_source(
                    tax_count=int(values["tax_count"]),
                    total_count=int(values["count"]),
                ),
            )
            for label, values in sorted_rows[:limit]
        ]

    def build_product_details(
        self,
        *,
        rows: list[ImportRowModel],
        start_at: datetime,
        end_at: datetime,
        category_name: str | None,
        limit: int,
        product_costs: dict[str, Decimal],
        product_vat_rates: dict[str, Decimal],
    ) -> list[DashboardProductDetailRow]:
        aggregate: dict[tuple[str, str], dict[str, Decimal | int]] = defaultdict(
            lambda: {
                "revenue": Decimal("0"),
                "net_revenue": Decimal("0"),
                "vat_amount": Decimal("0"),
                "estimated_cogs_net": Decimal("0"),
                "quantity": Decimal("0"),
                "count": 0,
                "tax_count": 0,
                "cost_count": 0,
            }
        )

        for row in rows:
            payload = row.normalized_payload or {}
            if not self._is_in_period(payload, start_at=start_at, end_at=end_at):
                continue

            category = self._extract_text(
                payload.get("category_name"),
                fallback=self._unknown_category,
            )
            if category_name is not None and category != category_name:
                continue

            product = self._extract_text(
                payload.get("product_name"),
                fallback=self._unknown_product,
            )
            key = (product, category)
            gross_amount = self._parse_decimal(payload.get("gross_amount"))
            tax = calculate_payload_tax(
                payload=payload,
                gross_amount=gross_amount,
                product_vat_rates=product_vat_rates,
            )
            quantity = self._parse_decimal(payload.get("quantity"))
            unit_cost = self._lookup_unit_cost_optional(payload, product_costs)
            aggregate[key]["revenue"] += gross_amount
            aggregate[key]["quantity"] += quantity
            aggregate[key]["count"] += 1
            if tax.net_amount is not None and tax.vat_amount is not None:
                aggregate[key]["net_revenue"] += tax.net_amount
                aggregate[key]["vat_amount"] += tax.vat_amount
                aggregate[key]["tax_count"] += 1
            if unit_cost is not None:
                aggregate[key]["estimated_cogs_net"] += unit_cost * quantity
                aggregate[key]["cost_count"] += 1

        sorted_rows = sorted(
            aggregate.items(),
            key=lambda item: Decimal(item[1]["revenue"]),
            reverse=True,
        )
        return [
            self._build_product_detail_row(product, category, values)
            for (product, category), values in sorted_rows[:limit]
        ]

    def build_product_source_rows(
        self,
        *,
        rows: list[ImportRowModel],
        start_at: datetime,
        end_at: datetime,
        product_name: str,
        category_name: str | None,
        limit: int,
        product_vat_rates: dict[str, Decimal],
    ) -> list[DashboardPosSourceRow]:
        source_rows: list[DashboardPosSourceRow] = []
        for row in rows:
            payload = row.normalized_payload or {}
            if not self._is_in_period(payload, start_at=start_at, end_at=end_at):
                continue

            category = self._extract_text(
                payload.get("category_name"),
                fallback=self._unknown_category,
            )
            product = self._extract_text(
                payload.get("product_name"),
                fallback=self._unknown_product,
            )
            if product != product_name:
                continue
            if category_name is not None and category != category_name:
                continue

            tax = calculate_payload_tax(
                payload=payload,
                gross_amount=self._parse_decimal(payload.get("gross_amount")),
                product_vat_rates=product_vat_rates,
            )
            source_rows.append(
                DashboardPosSourceRow(
                    row_id=row.id,
                    row_number=row.row_number,
                    date=self._parse_payload_date(payload.get("date")),
                    receipt_no=self._extract_optional_text(payload.get("receipt_no")),
                    category_name=category,
                    product_name=product,
                    quantity=self._parse_decimal(payload.get("quantity")),
                    gross_amount=self._parse_decimal(payload.get("gross_amount")),
                    net_amount=tax.net_amount,
                    vat_amount=tax.vat_amount,
                    vat_rate_percent=tax.vat_rate_percent,
                    payment_method=self._extract_optional_text(
                        payload.get("payment_method")
                    ),
                    source_layer="import_derived",
                    amount_basis="gross",
                    tax_breakdown_source=tax.source,
                )
            )

        return sorted(
            source_rows,
            key=lambda item: (item.date or date.min, item.row_number),
            reverse=True,
        )[:limit]

    def build_basket_metrics(
        self,
        *,
        rows: list[ImportRowModel],
        start_at: datetime,
        end_at: datetime,
    ) -> tuple[Decimal, Decimal]:
        baskets: dict[str, dict[str, Decimal]] = defaultdict(
            lambda: {"gross_amount": Decimal("0"), "quantity": Decimal("0")}
        )

        for row in rows:
            payload = row.normalized_payload or {}
            if not self._is_in_period(payload, start_at=start_at, end_at=end_at):
                continue

            receipt_no = self._extract_optional_text(payload.get("receipt_no"))
            basket_key = receipt_no or str(row.id)
            baskets[basket_key]["gross_amount"] += self._parse_decimal(
                payload.get("gross_amount")
            )
            baskets[basket_key]["quantity"] += self._parse_decimal(
                payload.get("quantity")
            )

        basket_count = len(baskets)
        if basket_count == 0:
            return Decimal("0"), Decimal("0")

        total_amount = sum(
            (values["gross_amount"] for values in baskets.values()),
            Decimal("0"),
        )
        total_quantity = sum(
            (values["quantity"] for values in baskets.values()),
            Decimal("0"),
        )
        return total_amount / basket_count, total_quantity / basket_count

    def build_basket_value_distribution(
        self,
        *,
        rows: list[ImportRowModel],
        start_at: datetime,
        end_at: datetime,
    ) -> list[DashboardBreakdownRow]:
        baskets: dict[str, Decimal] = defaultdict(Decimal)

        for row in rows:
            payload = row.normalized_payload or {}
            if not self._is_in_period(payload, start_at=start_at, end_at=end_at):
                continue

            receipt_no = self._extract_optional_text(payload.get("receipt_no"))
            basket_key = receipt_no or str(row.id)
            baskets[basket_key] += self._parse_decimal(payload.get("gross_amount"))

        bands: tuple[tuple[str, Decimal, Decimal | None], ...] = (
            ("0-999", Decimal("0"), Decimal("999")),
            ("1000-2499", Decimal("1000"), Decimal("2499")),
            ("2500-4999", Decimal("2500"), Decimal("4999")),
            ("5000-9999", Decimal("5000"), Decimal("9999")),
            ("10000+", Decimal("10000"), None),
        )
        aggregate: dict[str, dict[str, Decimal | int]] = {
            label: {"revenue": Decimal("0"), "count": 0}
            for label, _lower, _upper in bands
        }

        for amount in baskets.values():
            for label, lower, upper in bands:
                if amount < lower or (upper is not None and amount > upper):
                    continue
                aggregate[label]["revenue"] += amount
                aggregate[label]["count"] += 1
                break

        return [
            DashboardBreakdownRow(
                label=label,
                revenue=Decimal(aggregate[label]["revenue"]),
                net_revenue=None,
                vat_amount=None,
                quantity=Decimal(aggregate[label]["count"]),
                transaction_count=int(aggregate[label]["count"]),
                source_layer="import_derived",
                amount_basis="gross",
                tax_breakdown_source="not_available",
            )
            for label, _lower, _upper in bands
        ]

    def build_basket_pairs(
        self,
        *,
        rows: list[ImportRowModel],
        start_at: datetime,
        end_at: datetime,
        limit: int,
    ) -> list[DashboardBasketPairRow]:
        baskets: dict[str, dict[str, Decimal]] = defaultdict(
            lambda: defaultdict(Decimal)
        )

        for row in rows:
            payload = row.normalized_payload or {}
            if not self._is_in_period(payload, start_at=start_at, end_at=end_at):
                continue

            product = self._extract_text(
                payload.get("product_name"),
                fallback=self._unknown_product,
            )
            if product == self._unknown_product:
                continue

            receipt_no = self._extract_optional_text(payload.get("receipt_no"))
            basket_key = receipt_no or str(row.id)
            baskets[basket_key][product] += self._parse_decimal(
                payload.get("gross_amount")
            )

        pair_aggregate: dict[tuple[str, str], dict[str, Decimal | int]] = defaultdict(
            lambda: {"basket_count": 0, "total_gross_amount": Decimal("0")}
        )
        for products in baskets.values():
            unique_products = sorted(products.keys())
            if len(unique_products) < 2:
                continue

            for product_a, product_b in combinations(unique_products, 2):
                pair = (product_a, product_b)
                pair_aggregate[pair]["basket_count"] += 1
                pair_aggregate[pair]["total_gross_amount"] += (
                    products[product_a] + products[product_b]
                )

        sorted_pairs = sorted(
            pair_aggregate.items(),
            key=lambda item: (
                int(item[1]["basket_count"]),
                Decimal(item[1]["total_gross_amount"]),
                item[0][0],
                item[0][1],
            ),
            reverse=True,
        )
        return [
            DashboardBasketPairRow(
                product_a=product_a,
                product_b=product_b,
                basket_count=int(values["basket_count"]),
                total_gross_amount=Decimal(values["total_gross_amount"]),
                source_layer="import_derived",
            )
            for (product_a, product_b), values in sorted_pairs[:limit]
        ]

    def build_basket_pair_receipts(
        self,
        *,
        rows: list[ImportRowModel],
        start_at: datetime,
        end_at: datetime,
        product_a: str,
        product_b: str,
        limit: int,
    ) -> list[DashboardBasketReceipt]:
        basket_rows: dict[str, list[ImportRowModel]] = defaultdict(list)

        for row in rows:
            payload = row.normalized_payload or {}
            if not self._is_in_period(payload, start_at=start_at, end_at=end_at):
                continue

            receipt_no = self._extract_optional_text(payload.get("receipt_no"))
            if receipt_no is not None:
                basket_rows[receipt_no].append(row)

        receipts: list[DashboardBasketReceipt] = []
        for receipt_no, receipt_rows in basket_rows.items():
            products = {
                self._extract_text(
                    (row.normalized_payload or {}).get("product_name"),
                    fallback=self._unknown_product,
                )
                for row in receipt_rows
            }
            if product_a not in products or product_b not in products:
                continue

            receipt_date = None
            total_gross_amount = Decimal("0")
            total_quantity = Decimal("0")
            lines: list[DashboardBasketReceiptLine] = []
            for row in sorted(receipt_rows, key=lambda item: item.row_number):
                payload = row.normalized_payload or {}
                receipt_date = receipt_date or self._parse_payload_date(
                    payload.get("date")
                )
                quantity = self._parse_decimal(payload.get("quantity"))
                gross_amount = self._parse_decimal(payload.get("gross_amount"))
                total_quantity += quantity
                total_gross_amount += gross_amount
                lines.append(
                    DashboardBasketReceiptLine(
                        row_id=row.id,
                        row_number=row.row_number,
                        product_name=self._extract_text(
                            payload.get("product_name"),
                            fallback=self._unknown_product,
                        ),
                        category_name=self._extract_text(
                            payload.get("category_name"),
                            fallback=self._unknown_category,
                        ),
                        quantity=quantity,
                        gross_amount=gross_amount,
                        payment_method=self._extract_optional_text(
                            payload.get("payment_method")
                        ),
                    )
                )

            receipts.append(
                DashboardBasketReceipt(
                    receipt_no=receipt_no,
                    date=receipt_date,
                    gross_amount=total_gross_amount,
                    quantity=total_quantity,
                    lines=tuple(lines),
                    source_layer="import_derived",
                )
            )

        return sorted(
            receipts,
            key=lambda item: (item.date or date.min, item.gross_amount, item.receipt_no),
            reverse=True,
        )[:limit]

    def _build_product_detail_row(
        self,
        product: str,
        category: str,
        values: dict[str, Decimal | int],
    ) -> DashboardProductDetailRow:
        tax_count = int(values["tax_count"])
        cost_count = int(values["cost_count"])
        total_count = int(values["count"])
        quantity = Decimal(values["quantity"])
        net_revenue = Decimal(values["net_revenue"]) if tax_count > 0 else None
        vat_amount = Decimal(values["vat_amount"]) if tax_count > 0 else None
        estimated_cogs = (
            Decimal(values["estimated_cogs_net"]) if cost_count > 0 else None
        )
        estimated_unit_cost = (
            estimated_cogs / quantity
            if estimated_cogs is not None and quantity > Decimal("0")
            else None
        )
        estimated_net_margin = (
            net_revenue - estimated_cogs
            if net_revenue is not None and estimated_cogs is not None
            else None
        )
        estimated_margin_percent = (
            estimated_net_margin / net_revenue * Decimal("100")
            if estimated_net_margin is not None
            and net_revenue is not None
            and net_revenue > Decimal("0")
            else None
        )

        return DashboardProductDetailRow(
            product_name=product,
            category_name=category,
            revenue=Decimal(values["revenue"]),
            net_revenue=net_revenue,
            vat_amount=vat_amount,
            estimated_unit_cost_net=estimated_unit_cost,
            estimated_cogs_net=estimated_cogs,
            estimated_net_margin_amount=estimated_net_margin,
            estimated_margin_percent=estimated_margin_percent,
            quantity=quantity,
            transaction_count=total_count,
            source_layer="import_derived",
            amount_basis="gross",
            tax_breakdown_source=tax_breakdown_source(
                tax_count=tax_count,
                total_count=total_count,
            ),
            cost_source=cost_source(
                cost_count=cost_count,
                total_count=total_count,
            ),
            margin_status=margin_status(
                tax_count=tax_count,
                cost_count=cost_count,
                total_count=total_count,
            ),
        )

    def _is_in_period(
        self,
        payload: dict[str, Any],
        *,
        start_at: datetime,
        end_at: datetime,
    ) -> bool:
        occurred_at = self._payload_occurred_at(payload)
        return (
            occurred_at is not None
            and occurred_at >= start_at
            and occurred_at <= end_at
        )

    def _payload_occurred_at(self, payload: dict[str, Any]) -> datetime | None:
        occurred_at = payload.get("occurred_at")
        if isinstance(occurred_at, str):
            try:
                parsed = datetime.fromisoformat(occurred_at)
            except ValueError:
                parsed = None
            if parsed is not None:
                if parsed.tzinfo is None:
                    return parsed.replace(tzinfo=self._time_zone)
                return parsed.astimezone(self._time_zone)

        payload_date = self._parse_payload_date(payload.get("date"))
        if payload_date is None:
            return None
        return datetime(
            payload_date.year,
            payload_date.month,
            payload_date.day,
            tzinfo=self._time_zone,
        )

    def _iter_buckets(
        self,
        *,
        start_at: datetime,
        end_at: datetime,
        grain: str,
    ) -> list[datetime]:
        buckets: list[datetime] = []
        current = self._bucket_datetime(start_at, grain=grain)
        end_bucket = self._bucket_datetime(end_at, grain=grain)
        while current <= end_bucket:
            buckets.append(current)
            if grain == "month":
                current = (
                    current.replace(year=current.year + 1, month=1)
                    if current.month == 12
                    else current.replace(month=current.month + 1)
                )
            elif grain == "hour":
                current += timedelta(hours=1)
            else:
                current += timedelta(days=1)
        return buckets

    def _bucket_datetime(self, value: datetime, *, grain: str) -> datetime:
        local_value = (
            value.replace(tzinfo=self._time_zone)
            if value.tzinfo is None
            else value.astimezone(self._time_zone)
        )
        if grain == "month":
            return local_value.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if grain == "hour":
            return local_value.replace(minute=0, second=0, microsecond=0)
        return local_value.replace(hour=0, minute=0, second=0, microsecond=0)

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

    @classmethod
    def _lookup_unit_cost(
        cls,
        payload: dict[str, Any],
        product_costs: dict[str, Decimal],
    ) -> Decimal:
        return cls._lookup_unit_cost_optional(payload, product_costs) or Decimal("0")

    @staticmethod
    def _lookup_unit_cost_optional(
        payload: dict[str, Any],
        product_costs: dict[str, Decimal],
    ) -> Decimal | None:
        for key_name in ("product_id", "sku", "product_name"):
            value = payload.get(key_name)
            if isinstance(value, str) and value in product_costs:
                return product_costs[value]
        return None

    @staticmethod
    def _extract_text(value: Any, *, fallback: str) -> str:
        if isinstance(value, str) and value.strip():
            return value.strip()
        return fallback

    @staticmethod
    def _extract_optional_text(value: Any) -> str | None:
        if isinstance(value, str) and value.strip():
            return value.strip()
        return None
