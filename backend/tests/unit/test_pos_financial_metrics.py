"""Unit tests for pure POS financial metric helpers."""

from __future__ import annotations

from decimal import Decimal

from app.modules.analytics.infrastructure.repositories.pos_financial_metrics import (
    calculate_payload_tax,
    cost_source,
    lookup_payload_vat_rate,
    margin_status,
    payload_product_lookup_keys,
    tax_breakdown_source,
)


def test_product_lookup_keys_are_normalized_and_keep_priority() -> None:
    keys = payload_product_lookup_keys(
        {
            "product_id": "  Product-1 ",
            "sku": "ABC-12",
            "product_name": "Café Latte",
        }
    )

    assert keys == (
        "Product-1",
        "product-1",
        "ABC-12",
        "abc-12",
        "Café Latte",
        "café latte",
    )


def test_vat_rate_lookup_falls_back_to_casefolded_sku() -> None:
    rate = lookup_payload_vat_rate(
        {"sku": "ABC-12"},
        {"abc-12": Decimal("27")},
    )

    assert rate == Decimal("27")


def test_payload_tax_is_derived_from_gross_amount() -> None:
    tax = calculate_payload_tax(
        payload={"product_id": "product-1"},
        gross_amount=Decimal("1270"),
        product_vat_rates={"product-1": Decimal("27")},
    )

    assert tax.net_amount == Decimal("1000.00")
    assert tax.vat_amount == Decimal("270.00")
    assert tax.vat_rate_percent == Decimal("27")
    assert tax.source == "product_vat_derived"


def test_payload_tax_reports_missing_rate_without_fabricating_amounts() -> None:
    tax = calculate_payload_tax(
        payload={"product_name": "Unknown"},
        gross_amount=Decimal("1000"),
        product_vat_rates={},
    )

    assert tax.net_amount is None
    assert tax.vat_amount is None
    assert tax.vat_rate_percent is None
    assert tax.source == "not_available"


def test_coverage_sources_and_margin_statuses() -> None:
    assert tax_breakdown_source(tax_count=0, total_count=2) == "not_available"
    assert (
        tax_breakdown_source(tax_count=1, total_count=2)
        == "partial_product_vat_derived"
    )
    assert tax_breakdown_source(tax_count=2, total_count=2) == "product_vat_derived"

    assert cost_source(cost_count=0, total_count=2) == "not_available"
    assert cost_source(cost_count=1, total_count=2) == "partial_recipe_or_unit_cost"
    assert cost_source(cost_count=2, total_count=2) == "recipe_or_unit_cost"

    assert margin_status(tax_count=0, cost_count=0, total_count=0) == "no_data"
    assert (
        margin_status(tax_count=0, cost_count=0, total_count=2)
        == "missing_vat_and_cost"
    )
    assert margin_status(tax_count=0, cost_count=2, total_count=2) == "missing_vat_rate"
    assert margin_status(tax_count=2, cost_count=0, total_count=2) == "missing_cost"
    assert margin_status(tax_count=1, cost_count=1, total_count=2) == "partial"
    assert margin_status(tax_count=2, cost_count=2, total_count=2) == "complete"
