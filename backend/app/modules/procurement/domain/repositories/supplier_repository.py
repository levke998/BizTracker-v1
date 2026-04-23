"""Procurement supplier repository contract."""

from __future__ import annotations

import uuid
from typing import Protocol

from app.modules.procurement.domain.entities.supplier import NewSupplier, Supplier


class SupplierRepository(Protocol):
    """Defines persistence access for procurement suppliers."""

    def list_many(
        self,
        *,
        business_unit_id: uuid.UUID | None = None,
        is_active: bool | None = None,
        limit: int = 50,
    ) -> list[Supplier]:
        """List suppliers with lightweight filters."""

    def create(self, supplier: NewSupplier) -> Supplier:
        """Create one supplier."""

    def business_unit_exists(self, business_unit_id: uuid.UUID) -> bool:
        """Return whether the referenced business unit exists."""

    def exists_by_name(
        self,
        *,
        business_unit_id: uuid.UUID,
        name: str,
    ) -> bool:
        """Return whether a supplier with the same name already exists in the business unit."""
