"""List purchase invoices query."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from app.modules.procurement.domain.entities.purchase_invoice import PurchaseInvoice
from app.modules.procurement.domain.repositories.purchase_invoice_repository import (
    PurchaseInvoiceRepository,
)


@dataclass(slots=True)
class ListPurchaseInvoicesQuery:
    """Return purchase invoices with minimal filters."""

    repository: PurchaseInvoiceRepository

    def execute(
        self,
        *,
        business_unit_id: uuid.UUID | None = None,
        supplier_id: uuid.UUID | None = None,
        limit: int = 50,
    ) -> list[PurchaseInvoice]:
        return self.repository.list_many(
            business_unit_id=business_unit_id,
            supplier_id=supplier_id,
            limit=limit,
        )
