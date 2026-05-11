"""Upload a supplier invoice PDF into a review draft."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.master_data.infrastructure.orm.business_unit_model import (
    BusinessUnitModel,
)
from app.modules.master_data.infrastructure.orm.unit_of_measure_model import (
    UnitOfMeasureModel,
)
from app.modules.master_data.infrastructure.orm.vat_rate_model import VatRateModel
from app.modules.procurement.application.services.purchase_invoice_pdf_extraction import (
    PurchaseInvoicePdfExtractionResult,
    PurchaseInvoicePdfExtractionService,
    PurchaseInvoicePdfLineCandidate,
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

    def __init__(
        self,
        session: Session,
        storage_dir: Path,
        extraction_service: PurchaseInvoicePdfExtractionService | None = None,
    ) -> None:
        self._session = session
        self._storage_dir = storage_dir
        self._extraction_service = extraction_service or PurchaseInvoicePdfExtractionService()

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
        extraction = self._extraction_service.extract(content)

        draft = PurchaseInvoiceDraftModel(
            business_unit_id=business_unit_id,
            supplier_id=supplier_id,
            original_name=original_name,
            stored_path=str(stored_path),
            mime_type=mime_type,
            size_bytes=len(content),
            status="review_required",
            extraction_status=extraction.status,
            raw_extraction=extraction.to_raw_payload(),
            review_payload=self._build_review_payload(
                extraction=extraction,
                supplier_id=supplier_id,
            ),
            notes=self._build_notes(extraction.status),
        )
        self._session.add(draft)
        self._session.commit()
        self._session.refresh(draft)
        return draft

    def _build_review_payload(
        self,
        *,
        extraction: PurchaseInvoicePdfExtractionResult,
        supplier_id: uuid.UUID | None,
    ) -> dict:
        header = dict(extraction.header)
        if supplier_id is not None:
            header["supplier_id"] = str(supplier_id)
        if "currency" not in header:
            header["currency"] = "HUF"

        return {
            "header": header,
            "lines": [
                self._build_review_line(candidate=line, line_index=index)
                for index, line in enumerate(extraction.lines, start=1)
            ],
        }

    def _build_review_line(
        self,
        *,
        candidate: PurchaseInvoicePdfLineCandidate,
        line_index: int,
    ) -> dict:
        vat_rate = self._resolve_vat_rate(candidate.vat_rate_percent)
        uom = self._resolve_unit_of_measure(candidate.uom_code)
        issues = ["unreviewed_pdf_extraction"]
        if vat_rate is None:
            issues.append("missing_vat_rate")
        if uom is None:
            issues.append("missing_uom")

        return {
            "line_index": line_index,
            "description": candidate.description,
            "supplier_product_name": candidate.description,
            "inventory_item_id": None,
            "inventory_item_name": None,
            "quantity": self._decimal_to_string(candidate.quantity, Decimal("0.001")),
            "uom_id": str(uom.id) if uom else None,
            "vat_rate_id": str(vat_rate.id) if vat_rate else None,
            "vat_rate_percent": self._decimal_to_string(
                candidate.vat_rate_percent,
                Decimal("0.0001"),
            ),
            "unit_net_amount": self._calculate_unit_net_amount(candidate),
            "line_net_amount": self._decimal_to_string(candidate.line_net_amount),
            "vat_amount": self._decimal_to_string(candidate.vat_amount),
            "line_gross_amount": self._decimal_to_string(candidate.line_gross_amount),
            "calculation_status": "review_needed",
            "calculation_issues": issues,
            "extraction_confidence_score": self._decimal_to_string(
                candidate.confidence_score
            ),
            "extraction_confidence_reasons": list(candidate.confidence_reasons),
            "notes": "PDF text-layer prefill; user review is required.",
        }

    def _resolve_unit_of_measure(self, uom_code: str | None) -> UnitOfMeasureModel | None:
        if not uom_code:
            return None
        normalized_code = uom_code.strip().casefold()
        return self._session.scalar(
            select(UnitOfMeasureModel)
            .where(UnitOfMeasureModel.code.ilike(normalized_code))
            .limit(1)
        )

    def _resolve_vat_rate(self, rate_percent: Decimal | None) -> VatRateModel | None:
        if rate_percent is None:
            return None
        return self._session.scalar(
            select(VatRateModel)
            .where(VatRateModel.is_active.is_(True))
            .where(VatRateModel.rate_percent == rate_percent)
            .limit(1)
        )

    @staticmethod
    def _calculate_unit_net_amount(candidate: PurchaseInvoicePdfLineCandidate) -> str | None:
        if candidate.quantity is None or candidate.line_net_amount is None:
            return None
        if candidate.quantity == 0:
            return None
        return UploadPurchaseInvoicePdfDraftCommand._decimal_to_string(
            candidate.line_net_amount / candidate.quantity
        )

    @staticmethod
    def _decimal_to_string(
        value: Decimal | None,
        quant: Decimal = Decimal("0.01"),
    ) -> str | None:
        if value is None:
            return None
        return str(value.quantize(quant, rounding=ROUND_HALF_UP))

    @staticmethod
    def _build_notes(extraction_status: str) -> str:
        if extraction_status == "parsed_review_required":
            return "PDF uploaded; text-layer candidates were prefilled for review."
        if extraction_status == "no_candidates":
            return "PDF uploaded; no invoice candidates were found, manual review is required."
        if extraction_status == "no_text":
            return "PDF uploaded; no text layer was found, manual review is required."
        return "PDF uploaded; extraction/review is pending."
