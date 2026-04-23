"""Category list query use case."""

from __future__ import annotations

import uuid

from app.modules.master_data.application.dto.master_data_dto import CategoryDto
from app.modules.master_data.domain.repositories.category_repository import (
    CategoryRepository,
)


class ListCategoriesQuery:
    """Read-only use case for listing categories by business unit."""

    def __init__(self, repository: CategoryRepository) -> None:
        self._repository = repository

    def execute(
        self,
        business_unit_id: uuid.UUID,
        *,
        active_only: bool = True,
    ) -> list[CategoryDto]:
        items = self._repository.list_by_business_unit(
            business_unit_id,
            active_only=active_only,
        )
        return [
            CategoryDto(
                id=item.id,
                business_unit_id=item.business_unit_id,
                parent_id=item.parent_id,
                name=item.name,
                is_active=item.is_active,
            )
            for item in items
        ]
