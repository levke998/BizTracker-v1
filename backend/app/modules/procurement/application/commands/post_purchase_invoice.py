"""Post a purchase invoice into finance and actual inventory movements."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from app.modules.procurement.domain.repositories.purchase_invoice_repository import (
    PurchaseInvoicePostingResult,
    PurchaseInvoiceRepository,
)


class PurchaseInvoiceNotFoundError(Exception):
    """Raised when the selected purchase invoice does not exist."""


class PurchaseInvoiceAlreadyPostedError(Exception):
    """Raised when a purchase invoice was already posted to downstream actuals."""


@dataclass(slots=True)
class PostPurchaseInvoiceCommand:
    """Create downstream actual records from one manual supplier invoice."""

    repository: PurchaseInvoiceRepository

    def execute(self, *, purchase_invoice_id: uuid.UUID) -> PurchaseInvoicePostingResult:
        invoice = self.repository.get_by_id(purchase_invoice_id)
        if invoice is None:
            raise PurchaseInvoiceNotFoundError(
                f"Purchase invoice {purchase_invoice_id} was not found."
            )

        if self.repository.has_posting_for_invoice(purchase_invoice_id):
            raise PurchaseInvoiceAlreadyPostedError(
                "This purchase invoice has already been posted."
            )

        return self.repository.post_to_actuals(invoice)
