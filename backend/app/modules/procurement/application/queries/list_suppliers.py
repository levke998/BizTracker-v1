"""List suppliers query."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from app.modules.procurement.domain.entities.supplier import Supplier
from app.modules.procurement.domain.repositories.supplier_repository import (
    SupplierRepository,
)


@dataclass(slots=True)
class ListSuppliersQuery:
    """Return suppliers with minimal filters."""

    repository: SupplierRepository

    def execute(
        self,
        *,
        business_unit_id: uuid.UUID | None = None,
        is_active: bool | None = None,
        limit: int = 50,
    ) -> list[Supplier]:
        return self.repository.list_many(
            business_unit_id=business_unit_id,
            is_active=is_active,
            limit=limit,
        )
