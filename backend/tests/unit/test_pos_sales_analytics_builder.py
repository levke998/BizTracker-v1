"""Unit tests for the POS sales analytics read-model builder."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from types import SimpleNamespace
from zoneinfo import ZoneInfo

from app.modules.analytics.infrastructure.repositories.pos_sales_analytics_builder import (
    PosSalesAnalyticsBuilder,
)

TIME_ZONE = ZoneInfo("Europe/Budapest")
START_AT = datetime(2026, 6, 1, tzinfo=TIME_ZONE)
END_AT = datetime(2026, 6, 30, 23, 59, 59, tzinfo=TIME_ZONE)


def _builder() -> PosSalesAnalyticsBuilder:
    return PosSalesAnalyticsBuilder(
        time_zone=TIME_ZONE,
        unknown_category="Kategória nélkül",
        unknown_product="Ismeretlen termék",
    )


def _row(
    *,
    row_number: int,
    receipt_no: str,
    product_name: str,
    category_name: str = "Kávé",
    quantity: str = "1",
    gross_amount: str = "1270",
    sku: str = "SKU-1",
) -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid.uuid4(),
        row_number=row_number,
        normalized_payload={
            "date": "2026-06-10",
            "occurred_at": "2026-06-10T10:00:00+02:00",
            "receipt_no": receipt_no,
            "product_name": product_name,
            "category_name": category_name,
            "quantity": quantity,
            "gross_amount": gross_amount,
            "sku": sku,
            "payment_method": "card",
        },
    )


def test_basket_metrics_group_rows_by_receipt() -> None:
    rows = [
        _row(row_number=1, receipt_no="R-1", product_name="Latte"),
        _row(
            row_number=2,
            receipt_no="R-1",
            product_name="Espresso",
            gross_amount="730",
        ),
        _row(
            row_number=3,
            receipt_no="R-2",
            product_name="Tea",
            quantity="2",
            gross_amount="1000",
        ),
    ]

    average_value, average_quantity = _builder().build_basket_metrics(
        rows=rows,
        start_at=START_AT,
        end_at=END_AT,
    )

    assert average_value == Decimal("1500")
    assert average_quantity == Decimal("2")


def test_breakdown_keeps_partial_vat_coverage_explicit() -> None:
    rows = [
        _row(row_number=1, receipt_no="R-1", product_name="Latte"),
        _row(
            row_number=2,
            receipt_no="R-2",
            product_name="Unknown",
            gross_amount="1000",
            sku="MISSING",
        ),
    ]

    result = _builder().build_breakdown(
        rows=rows,
        start_at=START_AT,
        end_at=END_AT,
        key_name="category_name",
        fallback="Kategória nélkül",
        limit=10,
        product_vat_rates={"sku-1": Decimal("27")},
    )

    assert len(result) == 1
    assert result[0].revenue == Decimal("2270")
    assert result[0].net_revenue == Decimal("1000.00")
    assert result[0].vat_amount == Decimal("270.00")
    assert result[0].tax_breakdown_source == "partial_product_vat_derived"


def test_product_details_combine_net_revenue_and_estimated_cost() -> None:
    result = _builder().build_product_details(
        rows=[_row(row_number=1, receipt_no="R-1", product_name="Latte")],
        start_at=START_AT,
        end_at=END_AT,
        category_name=None,
        limit=10,
        product_costs={"Latte": Decimal("400")},
        product_vat_rates={"sku-1": Decimal("27")},
    )

    assert len(result) == 1
    product = result[0]
    assert product.net_revenue == Decimal("1000.00")
    assert product.estimated_cogs_net == Decimal("400")
    assert product.estimated_net_margin_amount == Decimal("600.00")
    assert product.estimated_margin_percent == Decimal("60.0")
    assert product.margin_status == "complete"


def test_rows_outside_selected_period_do_not_affect_cogs() -> None:
    row = _row(row_number=1, receipt_no="R-1", product_name="Latte")
    row.normalized_payload["occurred_at"] = "2026-05-31T10:00:00+02:00"

    result = _builder().sum_estimated_cogs(
        rows=[row],
        product_costs={"Latte": Decimal("400")},
        start_at=START_AT,
        end_at=END_AT,
    )

    assert result == Decimal("0")


def test_basket_pairs_and_receipt_drilldown_use_the_same_receipt_grouping() -> None:
    rows = [
        _row(row_number=1, receipt_no="R-1", product_name="Latte"),
        _row(
            row_number=2,
            receipt_no="R-1",
            product_name="Croissant",
            gross_amount="730",
            sku="SKU-2",
        ),
        _row(row_number=3, receipt_no="R-2", product_name="Latte"),
    ]
    builder = _builder()

    pairs = builder.build_basket_pairs(
        rows=rows,
        start_at=START_AT,
        end_at=END_AT,
        limit=10,
    )
    receipts = builder.build_basket_pair_receipts(
        rows=rows,
        start_at=START_AT,
        end_at=END_AT,
        product_a="Croissant",
        product_b="Latte",
        limit=10,
    )

    assert len(pairs) == 1
    assert pairs[0].product_a == "Croissant"
    assert pairs[0].product_b == "Latte"
    assert pairs[0].basket_count == 1
    assert pairs[0].total_gross_amount == Decimal("2000")

    assert len(receipts) == 1
    assert receipts[0].receipt_no == "R-1"
    assert receipts[0].gross_amount == Decimal("2000")
    assert [line.product_name for line in receipts[0].lines] == [
        "Latte",
        "Croissant",
    ]
