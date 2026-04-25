"""Minimal import-type specific parser profiles."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class HeaderValidationError:
    """Represents one structural header validation problem."""

    error_code: str
    message: str
    raw_payload: dict[str, object] | None = None


class PosSalesImportProfile:
    """Minimal structural checks for the pos_sales import type."""

    required_headers = (
        "date",
        "receipt_no",
        "product_name",
        "quantity",
        "gross_amount",
        "payment_method",
    )

    def validate_headers(
        self,
        *,
        normalized_headers: list[str],
    ) -> HeaderValidationError | None:
        missing_headers = [
            header for header in self.required_headers if header not in normalized_headers
        ]
        if not missing_headers:
            return None

        return HeaderValidationError(
            error_code="missing_required_columns",
            message=(
                "The pos_sales import is missing required columns: "
                + ", ".join(missing_headers)
                + "."
            ),
            raw_payload={
                "required_headers": list(self.required_headers),
                "normalized_headers": normalized_headers,
                "missing_headers": missing_headers,
            },
        )

    def normalize_row(self, *, raw_payload: dict[str, Any]) -> dict[str, Any]:
        """Apply light field-level normalization for later mapping steps."""

        return {
            "date": self._normalize_text(raw_payload.get("date")),
            "receipt_no": self._normalize_text(raw_payload.get("receipt_no")),
            "product_id": self._normalize_text(raw_payload.get("product_id")),
            "sku": self._normalize_text(raw_payload.get("sku")),
            "category_name": self._normalize_text(raw_payload.get("category_name")),
            "product_name": self._normalize_text(raw_payload.get("product_name")),
            "quantity": self._normalize_number(raw_payload.get("quantity")),
            "gross_amount": self._normalize_number(raw_payload.get("gross_amount")),
            "payment_method": self._normalize_payment_method(
                raw_payload.get("payment_method")
            ),
        }

    @staticmethod
    def _normalize_text(value: Any) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str):
            return str(value)

        normalized = value.strip()
        return normalized or None

    def _normalize_payment_method(self, value: Any) -> str | None:
        normalized = self._normalize_text(value)
        if normalized is None:
            return None
        return normalized.lower()

    @staticmethod
    def _normalize_number(value: Any) -> int | float | str | None:
        if value is None:
            return None

        if isinstance(value, (int, float)):
            return value

        if not isinstance(value, str):
            return value

        normalized = value.strip()
        if not normalized:
            return None

        compact = normalized.replace(" ", "").replace(",", ".")

        try:
            numeric = float(compact)
        except ValueError:
            return normalized

        if numeric.is_integer():
            return int(numeric)
        return numeric


PROFILE_REGISTRY = {
    "pos_sales": PosSalesImportProfile(),
}


def get_import_profile(import_type: str):
    """Return a minimal profile object when one is defined."""

    return PROFILE_REGISTRY.get(import_type)
