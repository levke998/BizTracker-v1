"""Pure helpers for deriving POS financial metrics from normalized import rows."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from app.modules.finance.application.services.vat_calculator import VatCalculator


@dataclass(frozen=True, slots=True)
class PosTaxBreakdown:
    """Derived VAT breakdown for a POS row based on product master data."""

    net_amount: Decimal | None
    vat_amount: Decimal | None
    vat_rate_percent: Decimal | None
    source: str


def calculate_payload_tax(
    *,
    payload: dict[str, Any],
    gross_amount: Decimal,
    product_vat_rates: dict[str, Decimal],
) -> PosTaxBreakdown:
    """Calculate a POS row's VAT amounts when its product VAT rate is known."""

    rate_percent = lookup_payload_vat_rate(payload, product_vat_rates)
    if rate_percent is None:
        return PosTaxBreakdown(
            net_amount=None,
            vat_amount=None,
            vat_rate_percent=None,
            source="not_available",
        )

    result = VatCalculator().calculate_from_gross(
        gross_amount=gross_amount,
        rate_percent=rate_percent,
    )
    return PosTaxBreakdown(
        net_amount=result.net_amount,
        vat_amount=result.vat_amount,
        vat_rate_percent=rate_percent,
        source="product_vat_derived",
    )


def lookup_payload_vat_rate(
    payload: dict[str, Any],
    product_vat_rates: dict[str, Decimal],
) -> Decimal | None:
    """Resolve a VAT rate by product id, SKU, or unambiguous product name."""

    for key in payload_product_lookup_keys(payload):
        rate = product_vat_rates.get(key)
        if rate is not None:
            return rate
    return None


def payload_product_lookup_keys(payload: dict[str, Any]) -> tuple[str, ...]:
    """Return normalized product lookup keys in deterministic priority order."""

    keys: list[str] = []
    for key_name in ("product_id", "sku", "product_name"):
        value = payload.get(key_name)
        if isinstance(value, str) and value.strip():
            text = value.strip()
            keys.append(text)
            keys.append(text.casefold())
    return tuple(dict.fromkeys(keys))


def tax_breakdown_source(*, tax_count: int, total_count: int) -> str:
    if tax_count <= 0:
        return "not_available"
    if tax_count == total_count:
        return "product_vat_derived"
    return "partial_product_vat_derived"


def cost_source(*, cost_count: int, total_count: int) -> str:
    if cost_count <= 0:
        return "not_available"
    if cost_count == total_count:
        return "recipe_or_unit_cost"
    return "partial_recipe_or_unit_cost"


def margin_status(*, tax_count: int, cost_count: int, total_count: int) -> str:
    if total_count <= 0:
        return "no_data"

    has_complete_tax = tax_count == total_count
    has_complete_cost = cost_count == total_count
    if has_complete_tax and has_complete_cost:
        return "complete"
    if tax_count <= 0 and cost_count <= 0:
        return "missing_vat_and_cost"
    if tax_count <= 0:
        return "missing_vat_rate"
    if cost_count <= 0:
        return "missing_cost"
    return "partial"
