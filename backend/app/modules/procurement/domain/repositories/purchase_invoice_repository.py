"""Procurement purchase invoice repository contract."""

from __future__ import annotations

import uuid
from typing import Protocol

from app.modules.procurement.domain.entities.purchase_invoice import (
    NewPurchaseInvoice,
    PurchaseInvoice,
)


class PurchaseInvoiceRepository(Protocol):
    """Defines persistence access for procurement purchase invoices."""

    def list_many(
        self,
        *,
        business_unit_id: uuid.UUID | None = None,
        supplier_id: uuid.UUID | None = None,
        limit: int = 50,
    ) -> list[PurchaseInvoice]:
        """List purchase invoices with lightweight filters."""

    def create(self, invoice: NewPurchaseInvoice) -> PurchaseInvoice:
        """Create one purchase invoice with its lines."""

    def business_unit_exists(self, business_unit_id: uuid.UUID) -> bool:
        """Return whether the referenced business unit exists."""

    def supplier_exists(self, supplier_id: uuid.UUID) -> bool:
        """Return whether the referenced supplier exists."""

    def supplier_belongs_to_business_unit(
        self,
        *,
        supplier_id: uuid.UUID,
        business_unit_id: uuid.UUID,
    ) -> bool:
        """Return whether the supplier belongs to the selected business unit."""

    def invoice_number_exists(
        self,
        *,
        business_unit_id: uuid.UUID,
        supplier_id: uuid.UUID,
        invoice_number: str,
    ) -> bool:
        """Return whether the supplier invoice number already exists in this business unit."""

    def unit_of_measure_exists(self, uom_id: uuid.UUID) -> bool:
        """Return whether the referenced unit of measure exists."""

    def inventory_item_exists(self, inventory_item_id: uuid.UUID) -> bool:
        """Return whether the referenced inventory item exists."""

    def inventory_item_belongs_to_business_unit(
        self,
        *,
        inventory_item_id: uuid.UUID,
        business_unit_id: uuid.UUID,
    ) -> bool:
        """Return whether the inventory item belongs to the selected business unit."""

    def inventory_item_matches_uom(
        self,
        *,
        inventory_item_id: uuid.UUID,
        uom_id: uuid.UUID,
    ) -> bool:
        """Return whether the inventory item uses the provided unit of measure."""
