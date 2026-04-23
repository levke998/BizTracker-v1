"""Minimal import-type specific parser profiles."""

from __future__ import annotations

from dataclasses import dataclass


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


PROFILE_REGISTRY = {
    "pos_sales": PosSalesImportProfile(),
}


def get_import_profile(import_type: str):
    """Return a minimal profile object when one is defined."""

    return PROFILE_REGISTRY.get(import_type)
