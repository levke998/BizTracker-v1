"""Create supplier use case."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from app.modules.procurement.domain.entities.supplier import NewSupplier, Supplier
from app.modules.procurement.domain.repositories.supplier_repository import (
    SupplierRepository,
)


class ProcurementBusinessUnitNotFoundError(Exception):
    """Raised when the selected business unit does not exist."""


class SupplierAlreadyExistsError(Exception):
    """Raised when a supplier with the same name already exists in the business unit."""


@dataclass(slots=True)
class CreateSupplierCommand:
    """Create a procurement supplier with minimal validation."""

    repository: SupplierRepository

    def execute(
        self,
        *,
        business_unit_id: uuid.UUID,
        name: str,
        tax_id: str | None = None,
        contact_name: str | None = None,
        email: str | None = None,
        phone: str | None = None,
        notes: str | None = None,
        is_active: bool = True,
    ) -> Supplier:
        normalized_name = name.strip()

        if not self.repository.business_unit_exists(business_unit_id):
            raise ProcurementBusinessUnitNotFoundError(
                f"Business unit {business_unit_id} was not found."
            )
        if self.repository.exists_by_name(
            business_unit_id=business_unit_id,
            name=normalized_name,
        ):
            raise SupplierAlreadyExistsError(
                "A supplier with the same name already exists in this business unit."
            )

        return self.repository.create(
            NewSupplier(
                business_unit_id=business_unit_id,
                name=normalized_name,
                tax_id=tax_id.strip() if tax_id else None,
                contact_name=contact_name.strip() if contact_name else None,
                email=email.strip() if email else None,
                phone=phone.strip() if phone else None,
                notes=notes.strip() if notes else None,
                is_active=is_active,
            )
        )
