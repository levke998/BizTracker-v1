"""VAT calculation service for finance/accounting-ready flows."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

MONEY_QUANT = Decimal("0.01")
PERCENT_BASE = Decimal("100")


class VatCalculationError(ValueError):
    """Raised when VAT calculation input is incomplete or invalid."""


@dataclass(frozen=True, slots=True)
class VatCalculationResult:
    """Normalized VAT calculation result."""

    net_amount: Decimal
    vat_amount: Decimal
    gross_amount: Decimal
    rate_percent: Decimal
    status: str
    issues: tuple[str, ...] = ()


class VatCalculator:
    """Calculate and reconcile net/gross/VAT amounts with Decimal arithmetic."""

    def calculate_from_gross(
        self,
        *,
        gross_amount: Decimal,
        rate_percent: Decimal,
    ) -> VatCalculationResult:
        self._validate_non_negative(gross_amount, "gross_amount")
        factor = self._factor(rate_percent)
        net_amount = self._money(gross_amount / factor)
        vat_amount = self._money(gross_amount - net_amount)
        return VatCalculationResult(
            net_amount=net_amount,
            vat_amount=vat_amount,
            gross_amount=self._money(gross_amount),
            rate_percent=rate_percent,
            status="ok",
        )

    def calculate_from_net(
        self,
        *,
        net_amount: Decimal,
        rate_percent: Decimal,
    ) -> VatCalculationResult:
        self._validate_non_negative(net_amount, "net_amount")
        factor = self._factor(rate_percent)
        gross_amount = self._money(net_amount * factor)
        vat_amount = self._money(gross_amount - net_amount)
        return VatCalculationResult(
            net_amount=self._money(net_amount),
            vat_amount=vat_amount,
            gross_amount=gross_amount,
            rate_percent=rate_percent,
            status="ok",
        )

    def reconcile(
        self,
        *,
        rate_percent: Decimal,
        net_amount: Decimal | None = None,
        vat_amount: Decimal | None = None,
        gross_amount: Decimal | None = None,
        tolerance: Decimal = Decimal("1.00"),
    ) -> VatCalculationResult:
        """Return calculated amounts and review status for provided invoice values."""

        if net_amount is None and gross_amount is None:
            raise VatCalculationError("Either net_amount or gross_amount is required.")
        self._validate_non_negative(tolerance, "tolerance")

        base = (
            self.calculate_from_gross(gross_amount=gross_amount, rate_percent=rate_percent)
            if gross_amount is not None
            else self.calculate_from_net(net_amount=net_amount or Decimal("0"), rate_percent=rate_percent)
        )
        issues: list[str] = []

        if net_amount is not None:
            self._validate_non_negative(net_amount, "net_amount")
            if abs(self._money(net_amount) - base.net_amount) > tolerance:
                issues.append("net_amount_mismatch")
        if vat_amount is not None:
            self._validate_non_negative(vat_amount, "vat_amount")
            if abs(self._money(vat_amount) - base.vat_amount) > tolerance:
                issues.append("vat_amount_mismatch")
        if gross_amount is not None:
            self._validate_non_negative(gross_amount, "gross_amount")
            if abs(self._money(gross_amount) - base.gross_amount) > tolerance:
                issues.append("gross_amount_mismatch")

        return VatCalculationResult(
            net_amount=base.net_amount if net_amount is None else self._money(net_amount),
            vat_amount=base.vat_amount if vat_amount is None else self._money(vat_amount),
            gross_amount=base.gross_amount if gross_amount is None else self._money(gross_amount),
            rate_percent=rate_percent,
            status="review_needed" if issues else "ok",
            issues=tuple(issues),
        )

    def _factor(self, rate_percent: Decimal) -> Decimal:
        self._validate_non_negative(rate_percent, "rate_percent")
        return Decimal("1") + (rate_percent / PERCENT_BASE)

    @staticmethod
    def _money(value: Decimal) -> Decimal:
        return value.quantize(MONEY_QUANT, rounding=ROUND_HALF_UP)

    @staticmethod
    def _validate_non_negative(value: Decimal, field_name: str) -> None:
        if value < 0:
            raise VatCalculationError(f"{field_name} cannot be negative.")
