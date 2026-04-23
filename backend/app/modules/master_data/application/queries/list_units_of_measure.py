"""Unit-of-measure list query use case."""

from __future__ import annotations

from app.modules.master_data.application.dto.master_data_dto import UnitOfMeasureDto
from app.modules.master_data.domain.repositories.unit_of_measure_repository import (
    UnitOfMeasureRepository,
)


class ListUnitsOfMeasureQuery:
    """Read-only use case for listing units of measure."""

    def __init__(self, repository: UnitOfMeasureRepository) -> None:
        self._repository = repository

    def execute(self) -> list[UnitOfMeasureDto]:
        items = self._repository.list_all()
        return [
            UnitOfMeasureDto(
                id=item.id,
                code=item.code,
                name=item.name,
                symbol=item.symbol,
            )
            for item in items
        ]
