"""VAT rate list query use case."""

from __future__ import annotations

from app.modules.master_data.application.dto.master_data_dto import VatRateDto
from app.modules.master_data.domain.repositories.vat_rate_repository import (
    VatRateRepository,
)


class ListVatRatesQuery:
    """Read-only use case for listing VAT rates."""

    def __init__(self, repository: VatRateRepository) -> None:
        self._repository = repository

    def execute(self, *, active_only: bool = True) -> list[VatRateDto]:
        items = self._repository.list_all(active_only=active_only)
        return [
            VatRateDto(
                id=item.id,
                code=item.code,
                name=item.name,
                rate_percent=item.rate_percent,
                rate_type=item.rate_type,
                nav_code=item.nav_code,
                description=item.description,
                valid_from=item.valid_from,
                valid_to=item.valid_to,
                is_active=item.is_active,
            )
            for item in items
        ]
