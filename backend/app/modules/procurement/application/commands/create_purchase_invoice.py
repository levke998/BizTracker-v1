"""Create purchase invoice use case."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from app.modules.procurement.domain.entities.purchase_invoice import (
    NewPurchaseInvoice,
    NewPurchaseInvoiceLine,
    PurchaseInvoice,
)
from app.modules.procurement.domain.repositories.purchase_invoice_repository import (
    PurchaseInvoiceRepository,
)


class ProcurementInvoiceBusinessUnitNotFoundError(Exception):
    """Raised when the selected business unit does not exist."""


class ProcurementInvoiceSupplierNotFoundError(Exception):
    """Raised when the selected supplier does not exist."""


class ProcurementInvoiceSupplierMismatchError(Exception):
    """Raised when the supplier does not belong to the selected business unit."""


class ProcurementInvoiceAlreadyExistsError(Exception):
    """Raised when the invoice number already exists for the same supplier and business unit."""


class ProcurementInvoiceUnitOfMeasureNotFoundError(Exception):
    """Raised when a referenced unit of measure does not exist."""


class ProcurementInvoiceInventoryItemNotFoundError(Exception):
    """Raised when a referenced inventory item does not exist."""


class ProcurementInvoiceInventoryItemMismatchError(Exception):
    """Raised when the inventory item does not belong to the selected business unit."""


class ProcurementInvoiceInventoryItemUnitMismatchError(Exception):
    """Raised when the inventory item uses a different unit of measure."""


@dataclass(frozen=True, slots=True)
class CreatePurchaseInvoiceLineInput:
    """One draft purchase invoice line coming from the API layer."""

    inventory_item_id: uuid.UUID | None
    description: str
    quantity: Decimal
    uom_id: uuid.UUID
    unit_net_amount: Decimal
    line_net_amount: Decimal


@dataclass(slots=True)
class CreatePurchaseInvoiceCommand:
    """Create a procurement purchase invoice with minimal validation."""

    repository: PurchaseInvoiceRepository

    def execute(
        self,
        *,
        business_unit_id: uuid.UUID,
        supplier_id: uuid.UUID,
        invoice_number: str,
        invoice_date: date,
        currency: str,
        gross_total: Decimal,
        notes: str | None = None,
        lines: tuple[CreatePurchaseInvoiceLineInput, ...],
    ) -> PurchaseInvoice:
        normalized_invoice_number = invoice_number.strip()
        normalized_currency = currency.strip().upper()

        if not self.repository.business_unit_exists(business_unit_id):
            raise ProcurementInvoiceBusinessUnitNotFoundError(
                f"Business unit {business_unit_id} was not found."
            )
        if not self.repository.supplier_exists(supplier_id):
            raise ProcurementInvoiceSupplierNotFoundError(
                f"Supplier {supplier_id} was not found."
            )
        if not self.repository.supplier_belongs_to_business_unit(
            supplier_id=supplier_id,
            business_unit_id=business_unit_id,
        ):
            raise ProcurementInvoiceSupplierMismatchError(
                "The supplier does not belong to the selected business unit."
            )
        if self.repository.invoice_number_exists(
            business_unit_id=business_unit_id,
            supplier_id=supplier_id,
            invoice_number=normalized_invoice_number,
        ):
            raise ProcurementInvoiceAlreadyExistsError(
                "A purchase invoice with the same supplier and invoice number already exists."
            )

        normalized_lines: list[NewPurchaseInvoiceLine] = []
        for line in lines:
            if not self.repository.unit_of_measure_exists(line.uom_id):
                raise ProcurementInvoiceUnitOfMeasureNotFoundError(
                    f"Unit of measure {line.uom_id} was not found."
                )

            if line.inventory_item_id is not None:
                if not self.repository.inventory_item_exists(line.inventory_item_id):
                    raise ProcurementInvoiceInventoryItemNotFoundError(
                        f"Inventory item {line.inventory_item_id} was not found."
                    )
                if not self.repository.inventory_item_belongs_to_business_unit(
                    inventory_item_id=line.inventory_item_id,
                    business_unit_id=business_unit_id,
                ):
                    raise ProcurementInvoiceInventoryItemMismatchError(
                        "The inventory item does not belong to the selected business unit."
                    )
                if not self.repository.inventory_item_matches_uom(
                    inventory_item_id=line.inventory_item_id,
                    uom_id=line.uom_id,
                ):
                    raise ProcurementInvoiceInventoryItemUnitMismatchError(
                        "The inventory item unit of measure does not match the provided line unit."
                    )

            normalized_lines.append(
                NewPurchaseInvoiceLine(
                    inventory_item_id=line.inventory_item_id,
                    description=line.description.strip(),
                    quantity=line.quantity,
                    uom_id=line.uom_id,
                    unit_net_amount=line.unit_net_amount,
                    line_net_amount=line.line_net_amount,
                )
            )

        return self.repository.create(
            NewPurchaseInvoice(
                business_unit_id=business_unit_id,
                supplier_id=supplier_id,
                invoice_number=normalized_invoice_number,
                invoice_date=invoice_date,
                currency=normalized_currency,
                gross_total=gross_total,
                notes=notes.strip() if notes else None,
                lines=tuple(normalized_lines),
            )
        )
