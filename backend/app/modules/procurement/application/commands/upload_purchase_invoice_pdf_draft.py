"""Upload a supplier invoice PDF into a review draft."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.master_data.infrastructure.orm.business_unit_model import (
    BusinessUnitModel,
)
from app.modules.procurement.infrastructure.orm.purchase_invoice_draft_model import (
    PurchaseInvoiceDraftModel,
)
from app.modules.procurement.infrastructure.orm.supplier_model import SupplierModel


class PurchaseInvoiceDraftValidationError(Exception):
    """Raised when an uploaded invoice draft is invalid."""


class PurchaseInvoiceDraftBusinessUnitNotFoundError(Exception):
    """Raised when the selected business unit does not exist."""


class PurchaseInvoiceDraftSupplierMismatchError(Exception):
    """Raised when the selected supplier cannot be used for the business unit."""


@dataclass(frozen=True, slots=True)
class PurchaseInvoicePdfDraft:
    """Read model for one uploaded PDF invoice draft."""

    id: uuid.UUID
    business_unit_id: uuid.UUID
    supplier_id: uuid.UUID | None
    original_name: str
    stored_path: str
    mime_type: str | None
    size_bytes: int
    status: str
    extraction_status: str
    raw_extraction: dict | None
    review_payload: dict | None
    notes: str | None


class UploadPurchaseInvoicePdfDraftCommand:
    """Persist one supplier invoice PDF as a review-required draft."""

    def __init__(self, session: Session, storage_dir: Path) -> None:
        self._session = session
        self._storage_dir = storage_dir

    def execute(
        self,
        *,
        business_unit_id: uuid.UUID,
        supplier_id: uuid.UUID | None,
        upload: UploadFile,
    ) -> PurchaseInvoiceDraftModel:
        business_unit_exists = self._session.scalar(
            select(BusinessUnitModel.id)
            .where(BusinessUnitModel.id == business_unit_id)
            .limit(1)
        )
        if business_unit_exists is None:
            raise PurchaseInvoiceDraftBusinessUnitNotFoundError(
                f"Business unit {business_unit_id} was not found."
            )

        if supplier_id is not None:
            supplier = self._session.get(SupplierModel, supplier_id)
            if supplier is None or supplier.business_unit_id != business_unit_id:
                raise PurchaseInvoiceDraftSupplierMismatchError(
                    "The selected supplier does not belong to the business unit."
                )

        original_name = Path(upload.filename or "supplier-invoice.pdf").name
        suffix = Path(original_name).suffix.lower()
        mime_type = upload.content_type
        if suffix != ".pdf" and mime_type != "application/pdf":
            raise PurchaseInvoiceDraftValidationError("Only PDF invoices can be uploaded.")

        content = upload.file.read()
        if not content:
            raise PurchaseInvoiceDraftValidationError("The uploaded PDF is empty.")

        target_dir = self._storage_dir / "purchase_invoice_pdfs" / str(business_unit_id)
        target_dir.mkdir(parents=True, exist_ok=True)
        stored_path = target_dir / f"{uuid.uuid4()}.pdf"
        stored_path.write_bytes(content)

        draft = PurchaseInvoiceDraftModel(
            business_unit_id=business_unit_id,
            supplier_id=supplier_id,
            original_name=original_name,
            stored_path=str(stored_path),
            mime_type=mime_type,
            size_bytes=len(content),
            status="review_required",
            extraction_status="not_started",
            raw_extraction=None,
            review_payload={"header": {}, "lines": []},
            notes="PDF uploaded; extraction/review is pending.",
        )
        self._session.add(draft)
        self._session.commit()
        self._session.refresh(draft)
        return draft
