"""Unit tests for VAT calculation service."""

from __future__ import annotations

from decimal import Decimal

import pytest

from app.modules.finance.application.services.vat_calculator import (
    VatCalculationError,
    VatCalculator,
)


def test_calculate_from_gross_uses_decimal_money_rounding() -> None:
    result = VatCalculator().calculate_from_gross(
        gross_amount=Decimal("1270"),
        rate_percent=Decimal("27"),
    )

    assert result.net_amount == Decimal("1000.00")
    assert result.vat_amount == Decimal("270.00")
    assert result.gross_amount == Decimal("1270.00")
    assert result.status == "ok"


def test_calculate_from_net_uses_decimal_money_rounding() -> None:
    result = VatCalculator().calculate_from_net(
        net_amount=Decimal("1000"),
        rate_percent=Decimal("5"),
    )

    assert result.net_amount == Decimal("1000.00")
    assert result.vat_amount == Decimal("50.00")
    assert result.gross_amount == Decimal("1050.00")


def test_reconcile_fills_missing_components_from_gross_and_rate() -> None:
    result = VatCalculator().reconcile(
        gross_amount=Decimal("1180"),
        rate_percent=Decimal("18"),
    )

    assert result.net_amount == Decimal("1000.00")
    assert result.vat_amount == Decimal("180.00")
    assert result.gross_amount == Decimal("1180.00")
    assert result.issues == ()


def test_reconcile_marks_review_needed_when_invoice_values_conflict() -> None:
    result = VatCalculator().reconcile(
        net_amount=Decimal("1000"),
        vat_amount=Decimal("300"),
        gross_amount=Decimal("1270"),
        rate_percent=Decimal("27"),
        tolerance=Decimal("0.01"),
    )

    assert result.status == "review_needed"
    assert result.issues == ("vat_amount_mismatch",)


def test_reconcile_allows_rounding_tolerance() -> None:
    result = VatCalculator().reconcile(
        net_amount=Decimal("999.99"),
        vat_amount=Decimal("270.01"),
        gross_amount=Decimal("1270"),
        rate_percent=Decimal("27"),
        tolerance=Decimal("1.00"),
    )

    assert result.status == "ok"


def test_negative_amount_raises_validation_error() -> None:
    with pytest.raises(VatCalculationError):
        VatCalculator().calculate_from_gross(
            gross_amount=Decimal("-1"),
            rate_percent=Decimal("27"),
        )
