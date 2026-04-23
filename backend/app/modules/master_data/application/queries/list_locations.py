"""Location list query use case."""

from __future__ import annotations

import uuid

from app.modules.master_data.application.dto.master_data_dto import LocationDto
from app.modules.master_data.domain.repositories.location_repository import (
    LocationRepository,
)


class ListLocationsQuery:
    """Read-only use case for listing locations by business unit."""

    def __init__(self, repository: LocationRepository) -> None:
        self._repository = repository

    def execute(
        self,
        business_unit_id: uuid.UUID,
        *,
        active_only: bool = True,
    ) -> list[LocationDto]:
        items = self._repository.list_by_business_unit(
            business_unit_id,
            active_only=active_only,
        )
        return [
            LocationDto(
                id=item.id,
                business_unit_id=item.business_unit_id,
                name=item.name,
                kind=item.kind,
                is_active=item.is_active,
            )
            for item in items
        ]
