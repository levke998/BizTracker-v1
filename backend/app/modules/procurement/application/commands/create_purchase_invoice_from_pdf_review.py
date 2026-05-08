"""Create a purchase invoice from a reviewed PDF draft."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy.orm import Session

from app.modules.procurement.application.commands.create_purchase_invoice import (
    CreatePurchaseInvoiceCommand,
    CreatePurchaseInvoiceLineInput,
    ProcurementInvoiceAlreadyExistsError,
    ProcurementInvoiceInventoryItemMismatchError,
    ProcurementInvoiceInventoryItemNotFoundError,
    ProcurementInvoiceInventoryItemUnitMismatchError,
    ProcurementInvoiceSupplierMismatchError,
    ProcurementInvoiceSupplierNotFoundError,
    ProcurementInvoiceUnitOfMeasureNotFoundError,
    ProcurementInvoiceVatRateNotFoundError,
)
from app.modules.procurement.domain.entities.purchase_invoice import PurchaseInvoice
from app.modules.procurement.domain.repositories.purchase_invoice_repository import (
    PurchaseInvoiceRepository,
)
from app.modules.procurement.infrastructure.orm.purchase_invoice_draft_model import (
    PurchaseInvoiceDraftModel,
)


class PurchaseInvoicePdfReviewDraftNotFoundError(Exception):
    """Raised when the selected PDF draft does not exist."""


class PurchaseInvoicePdfReviewNotReadyError(Exception):
    """Raised when a PDF draft cannot yet be converted to a purchase invoice."""


class PurchaseInvoicePdfReviewAlreadyConvertedError(Exception):
    """Raised when the PDF draft already produced a final purchase invoice."""


class PurchaseInvoicePdfReviewIncompleteError(Exception):
    """Raised when reviewed PDF data is missing invoice-required fields."""


@dataclass(slots=True)
class CreatePurchaseInvoiceFromPdfReviewCommand:
    """Convert one review-ready PDF draft into a final purchase invoice."""

    session: Session
    repository: PurchaseInvoiceRepository

    def execute(self, *, draft_id: uuid.UUID) -> PurchaseInvoice:
        draft = self.session.get(PurchaseInvoiceDraftModel, draft_id)
        if draft is None:
            raise PurchaseInvoicePdfReviewDraftNotFoundError(
                f"Purchase invoice PDF draft {draft_id} was not found."
            )
        if draft.status == "invoice_created":
            raise PurchaseInvoicePdfReviewAlreadyConvertedError(
                "This PDF draft has already been converted to a purchase invoice."
            )
        if draft.status != "review_ready":
            raise PurchaseInvoicePdfReviewNotReadyError(
                "The PDF draft must be review_ready before creating a purchase invoice."
            )

        payload = draft.review_payload or {}
        header = payload.get("header") or {}
        lines_payload = payload.get("lines") or []
        if not isinstance(header, dict) or not isinstance(lines_payload, list):
            raise PurchaseInvoicePdfReviewIncompleteError("The PDF review payload is invalid.")

        supplier_id = self._required_uuid(header.get("supplier_id"), "supplier")
        invoice_number = self._required_string(header.get("invoice_number"), "invoice_number")
        invoice_date = self._required_date(header.get("invoice_date"), "invoice_date")
        gross_total = self._required_decimal(header.get("gross_total"), "gross_total")
        currency = self._required_string(header.get("currency") or "HUF", "currency").upper()

        lines = tuple(
            self._line_input(line_payload, index=index)
            for index, line_payload in enumerate(lines_payload, start=1)
        )
        if not lines:
            raise PurchaseInvoicePdfReviewIncompleteError(
                "At least one reviewed invoice line is required."
            )

        creator = CreatePurchaseInvoiceCommand(repository=self.repository)
        invoice = creator.execute(
            business_unit_id=draft.business_unit_id,
            supplier_id=supplier_id,
            invoice_number=invoice_number,
            invoice_date=invoice_date,
            currency=currency,
            gross_total=gross_total,
            notes=header.get("notes") or f"Created from PDF draft {draft.original_name}.",
            lines=lines,
        )

        review_payload = dict(payload)
        review_payload["purchase_invoice_id"] = str(invoice.id)
        draft.review_payload = review_payload
        draft.status = "invoice_created"
        draft.notes = f"Purchase invoice {invoice.invoice_number} created from reviewed PDF."
        self.session.commit()
        self.session.refresh(draft)
        return invoice

    def _line_input(
        self,
        line_payload: object,
        *,
        index: int,
    ) -> CreatePurchaseInvoiceLineInput:
        if not isinstance(line_payload, dict):
            raise PurchaseInvoicePdfReviewIncompleteError(
                f"Review line {index} is invalid."
            )
        if line_payload.get("calculation_status") != "ok":
            raise PurchaseInvoicePdfReviewNotReadyError(
                f"Review line {index} must have ok calculation status."
            )

        quantity = self._required_decimal(line_payload.get("quantity"), f"line {index} quantity")
        line_net_amount = self._required_decimal(
            line_payload.get("line_net_amount"),
            f"line {index} line_net_amount",
        )
        unit_net_amount = self._optional_decimal(line_payload.get("unit_net_amount"))
        if unit_net_amount is None:
            unit_net_amount = (line_net_amount / quantity).quantize(
                Decimal("0.01"),
                rounding=ROUND_HALF_UP,
            )

        return CreatePurchaseInvoiceLineInput(
            inventory_item_id=self._optional_uuid(line_payload.get("inventory_item_id")),
            description=self._required_string(
                line_payload.get("description"),
                f"line {index} description",
            ),
            quantity=quantity,
            uom_id=self._required_uuid(line_payload.get("uom_id"), f"line {index} uom_id"),
            unit_net_amount=unit_net_amount,
            line_net_amount=line_net_amount,
            vat_rate_id=self._optional_uuid(line_payload.get("vat_rate_id")),
            vat_amount=self._optional_decimal(line_payload.get("vat_amount")),
            line_gross_amount=self._optional_decimal(line_payload.get("line_gross_amount")),
        )

    @staticmethod
    def _required_string(value: object, field_name: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise PurchaseInvoicePdfReviewIncompleteError(f"Missing {field_name}.")
        return value.strip()

    @staticmethod
    def _required_uuid(value: object, field_name: str) -> uuid.UUID:
        parsed = CreatePurchaseInvoiceFromPdfReviewCommand._optional_uuid(value)
        if parsed is None:
            raise PurchaseInvoicePdfReviewIncompleteError(f"Missing {field_name}.")
        return parsed

    @staticmethod
    def _optional_uuid(value: object) -> uuid.UUID | None:
        if value is None or value == "":
            return None
        try:
            return uuid.UUID(str(value))
        except ValueError as exc:
            raise PurchaseInvoicePdfReviewIncompleteError("Invalid UUID in review payload.") from exc

    @staticmethod
    def _required_date(value: object, field_name: str) -> date:
        if not isinstance(value, str) or not value.strip():
            raise PurchaseInvoicePdfReviewIncompleteError(f"Missing {field_name}.")
        try:
            return date.fromisoformat(value)
        except ValueError as exc:
            raise PurchaseInvoicePdfReviewIncompleteError(
                f"Invalid {field_name}."
            ) from exc

    @staticmethod
    def _required_decimal(value: object, field_name: str) -> Decimal:
        parsed = CreatePurchaseInvoiceFromPdfReviewCommand._optional_decimal(value)
        if parsed is None:
            raise PurchaseInvoicePdfReviewIncompleteError(f"Missing {field_name}.")
        if parsed <= 0:
            raise PurchaseInvoicePdfReviewIncompleteError(f"{field_name} must be positive.")
        return parsed

    @staticmethod
    def _optional_decimal(value: object) -> Decimal | None:
        if value is None or value == "":
            return None
        try:
            return Decimal(str(value))
        except Exception as exc:
            raise PurchaseInvoicePdfReviewIncompleteError(
                "Invalid decimal value in review payload."
            ) from exc


__all__ = [
    "CreatePurchaseInvoiceFromPdfReviewCommand",
    "PurchaseInvoiceAlreadyExistsError",
    "PurchaseInvoiceInventoryItemMismatchError",
    "PurchaseInvoiceInventoryItemNotFoundError",
    "PurchaseInvoiceInventoryItemUnitMismatchError",
    "PurchaseInvoicePdfReviewAlreadyConvertedError",
    "PurchaseInvoicePdfReviewDraftNotFoundError",
    "PurchaseInvoicePdfReviewIncompleteError",
    "PurchaseInvoicePdfReviewNotReadyError",
    "PurchaseInvoiceSupplierMismatchError",
    "PurchaseInvoiceSupplierNotFoundError",
    "PurchaseInvoiceUnitOfMeasureNotFoundError",
    "PurchaseInvoiceVatRateNotFoundError",
]
