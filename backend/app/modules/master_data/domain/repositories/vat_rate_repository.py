"""VAT rate repository contract."""

from __future__ import annotations

from typing import Protocol

from app.modules.master_data.domain.entities.vat_rate import VatRate


class VatRateRepository(Protocol):
    """Defines VAT rate read access."""

    def list_all(self, *, active_only: bool = True) -> list[VatRate]:
        """Return VAT rates ordered for user-facing selection."""
