"""Product list query use case."""

from __future__ import annotations

import uuid

from app.modules.master_data.application.dto.master_data_dto import ProductDto
from app.modules.master_data.domain.repositories.product_repository import (
    ProductRepository,
)


class ListProductsQuery:
    """Read-only use case for listing products by business unit."""

    def __init__(self, repository: ProductRepository) -> None:
        self._repository = repository

    def execute(
        self,
        business_unit_id: uuid.UUID,
        *,
        active_only: bool = True,
    ) -> list[ProductDto]:
        items = self._repository.list_by_business_unit(
            business_unit_id,
            active_only=active_only,
        )
        return [
            ProductDto(
                id=item.id,
                business_unit_id=item.business_unit_id,
                category_id=item.category_id,
                sku=item.sku,
                name=item.name,
                product_type=item.product_type,
                is_active=item.is_active,
            )
            for item in items
        ]
