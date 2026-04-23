"""Business unit list query use case."""

from __future__ import annotations

from app.modules.master_data.application.dto.master_data_dto import BusinessUnitDto
from app.modules.master_data.domain.repositories.business_unit_repository import (
    BusinessUnitRepository,
)


class ListBusinessUnitsQuery:
    """Read-only use case for listing business units."""

    def __init__(self, repository: BusinessUnitRepository) -> None:
        self._repository = repository

    def execute(self, *, active_only: bool = True) -> list[BusinessUnitDto]:
        items = self._repository.list_all(active_only=active_only)
        return [
            BusinessUnitDto(
                id=item.id,
                code=item.code,
                name=item.name,
                type=item.type,
                is_active=item.is_active,
            )
            for item in items
        ]
