"""Update supplier invoice PDF draft review data."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.finance.application.services.vat_calculator import (
    VatCalculationError,
    VatCalculator,
)
from app.modules.inventory.infrastructure.orm.inventory_item_model import (
    InventoryItemModel,
)
from app.modules.master_data.infrastructure.orm.unit_of_measure_model import (
    UnitOfMeasureModel,
)
from app.modules.master_data.infrastructure.orm.vat_rate_model import VatRateModel
from app.modules.procurement.infrastructure.orm.purchase_invoice_draft_model import (
    PurchaseInvoiceDraftModel,
)
from app.modules.procurement.infrastructure.orm.supplier_model import SupplierModel
from app.modules.procurement.infrastructure.orm.supplier_item_alias_model import (
    SupplierItemAliasModel,
)


class PurchaseInvoicePdfDraftNotFoundError(Exception):
    """Raised when the selected PDF draft does not exist."""


class PurchaseInvoicePdfReviewSupplierMismatchError(Exception):
    """Raised when a supplier does not belong to the draft business unit."""


class PurchaseInvoicePdfReviewInventoryItemMismatchError(Exception):
    """Raised when an inventory item cannot be used for the draft business unit."""


class PurchaseInvoicePdfReviewUnitOfMeasureNotFoundError(Exception):
    """Raised when a referenced unit of measure does not exist."""


class PurchaseInvoicePdfReviewVatRateNotFoundError(Exception):
    """Raised when a referenced VAT rate does not exist."""


@dataclass(frozen=True, slots=True)
class PurchaseInvoicePdfReviewLineInput:
    """One reviewed supplier invoice line."""

    description: str
    quantity: Decimal | None
    uom_id: uuid.UUID | None
    inventory_item_id: uuid.UUID | None
    vat_rate_id: uuid.UUID | None
    unit_net_amount: Decimal | None
    line_net_amount: Decimal | None
    vat_amount: Decimal | None
    line_gross_amount: Decimal | None
    supplier_product_name: str | None = None
    notes: str | None = None


@dataclass(frozen=True, slots=True)
class PurchaseInvoicePdfReviewInput:
    """Reviewed supplier invoice header and lines."""

    supplier_id: uuid.UUID | None
    invoice_number: str | None
    invoice_date: date | None
    currency: str
    gross_total: Decimal | None
    notes: str | None
    lines: tuple[PurchaseInvoicePdfReviewLineInput, ...]


class UpdatePurchaseInvoicePdfReviewCommand:
    """Persist reviewed PDF invoice fields and calculate VAT per line."""

    def __init__(self, session: Session, vat_calculator: VatCalculator | None = None) -> None:
        self._session = session
        self._vat_calculator = vat_calculator or VatCalculator()

    def execute(
        self,
        *,
        draft_id: uuid.UUID,
        review: PurchaseInvoicePdfReviewInput,
    ) -> PurchaseInvoiceDraftModel:
        draft = self._session.get(PurchaseInvoiceDraftModel, draft_id)
        if draft is None:
            raise PurchaseInvoicePdfDraftNotFoundError(
                f"Purchase invoice PDF draft {draft_id} was not found."
            )

        if review.supplier_id is not None:
            supplier = self._session.get(SupplierModel, review.supplier_id)
            if supplier is None or supplier.business_unit_id != draft.business_unit_id:
                raise PurchaseInvoicePdfReviewSupplierMismatchError(
                    "The selected supplier does not belong to the draft business unit."
                )

        reviewed_lines = [
            self._build_review_line(
                draft=draft,
                supplier_id=review.supplier_id,
                line=line,
                line_index=index,
            )
            for index, line in enumerate(review.lines, start=1)
        ]
        self._upsert_supplier_aliases(
            draft=draft,
            supplier_id=review.supplier_id,
            reviewed_lines=reviewed_lines,
        )
        all_lines_ok = bool(reviewed_lines) and all(
            line["calculation_status"] == "ok" for line in reviewed_lines
        )

        draft.supplier_id = review.supplier_id
        draft.review_payload = {
            "header": {
                "supplier_id": str(review.supplier_id) if review.supplier_id else None,
                "invoice_number": review.invoice_number.strip()
                if review.invoice_number
                else None,
                "invoice_date": review.invoice_date.isoformat()
                if review.invoice_date
                else None,
                "currency": review.currency.strip().upper(),
                "gross_total": self._decimal_to_string(review.gross_total),
                "notes": review.notes.strip() if review.notes else None,
            },
            "lines": reviewed_lines,
        }
        draft.status = "review_ready" if all_lines_ok else "review_required"
        draft.notes = (
            "PDF review saved; lines are calculation-ready."
            if all_lines_ok
            else "PDF review saved; at least one line still needs review."
        )

        self._session.commit()
        self._session.refresh(draft)
        return draft

    def _build_review_line(
        self,
        *,
        draft: PurchaseInvoiceDraftModel,
        supplier_id: uuid.UUID | None,
        line: PurchaseInvoicePdfReviewLineInput,
        line_index: int,
    ) -> dict:
        inventory_item = None
        inventory_item_id = line.inventory_item_id
        if inventory_item_id is None and supplier_id is not None and line.supplier_product_name:
            inventory_item_id = self._resolve_supplier_alias_item_id(
                business_unit_id=draft.business_unit_id,
                supplier_id=supplier_id,
                source_item_name=line.supplier_product_name,
            )

        if inventory_item_id is not None:
            inventory_item = self._session.get(InventoryItemModel, inventory_item_id)
            if (
                inventory_item is None
                or inventory_item.business_unit_id != draft.business_unit_id
            ):
                raise PurchaseInvoicePdfReviewInventoryItemMismatchError(
                    "The selected inventory item does not belong to the draft business unit."
                )

        if line.uom_id is not None and not self._exists_unit_of_measure(line.uom_id):
            raise PurchaseInvoicePdfReviewUnitOfMeasureNotFoundError(
                f"Unit of measure {line.uom_id} was not found."
            )

        vat_rate = None
        if line.vat_rate_id is not None:
            vat_rate = self._session.get(VatRateModel, line.vat_rate_id)
            if vat_rate is None:
                raise PurchaseInvoicePdfReviewVatRateNotFoundError(
                    f"VAT rate {line.vat_rate_id} was not found."
                )

        calculation = self._calculate_line(line=line, vat_rate=vat_rate)
        unit_net_amount = line.unit_net_amount
        if unit_net_amount is None and line.quantity and calculation["net_amount"]:
            unit_net_amount = (Decimal(calculation["net_amount"]) / line.quantity).quantize(
                Decimal("0.01"),
                rounding=ROUND_HALF_UP,
            )

        return {
            "line_index": line_index,
            "description": line.description.strip(),
            "supplier_product_name": line.supplier_product_name.strip()
            if line.supplier_product_name
            else None,
            "inventory_item_id": str(inventory_item_id)
            if inventory_item_id
            else None,
            "inventory_item_name": inventory_item.name if inventory_item else None,
            "quantity": self._decimal_to_string(line.quantity, Decimal("0.001")),
            "uom_id": str(line.uom_id) if line.uom_id else None,
            "vat_rate_id": str(line.vat_rate_id) if line.vat_rate_id else None,
            "vat_rate_percent": self._decimal_to_string(
                vat_rate.rate_percent,
                Decimal("0.0001"),
            )
            if vat_rate
            else None,
            "unit_net_amount": self._decimal_to_string(unit_net_amount),
            "line_net_amount": calculation["net_amount"],
            "vat_amount": calculation["vat_amount"],
            "line_gross_amount": calculation["gross_amount"],
            "calculation_status": calculation["status"],
            "calculation_issues": calculation["issues"],
            "notes": line.notes.strip() if line.notes else None,
        }

    def _calculate_line(
        self,
        *,
        line: PurchaseInvoicePdfReviewLineInput,
        vat_rate: VatRateModel | None,
    ) -> dict:
        issues: list[str] = []
        if vat_rate is None:
            issues.append("missing_vat_rate")
        if line.line_net_amount is None and line.line_gross_amount is None:
            issues.append("missing_net_or_gross_amount")
        if issues:
            return {
                "net_amount": self._decimal_to_string(line.line_net_amount),
                "vat_amount": self._decimal_to_string(line.vat_amount),
                "gross_amount": self._decimal_to_string(line.line_gross_amount),
                "status": "review_needed",
                "issues": issues,
            }

        try:
            result = self._vat_calculator.reconcile(
                rate_percent=Decimal(vat_rate.rate_percent),
                net_amount=line.line_net_amount,
                vat_amount=line.vat_amount,
                gross_amount=line.line_gross_amount,
            )
        except VatCalculationError as exc:
            return {
                "net_amount": self._decimal_to_string(line.line_net_amount),
                "vat_amount": self._decimal_to_string(line.vat_amount),
                "gross_amount": self._decimal_to_string(line.line_gross_amount),
                "status": "review_needed",
                "issues": [str(exc)],
            }

        return {
            "net_amount": self._decimal_to_string(result.net_amount),
            "vat_amount": self._decimal_to_string(result.vat_amount),
            "gross_amount": self._decimal_to_string(result.gross_amount),
            "status": result.status,
            "issues": list(result.issues),
        }

    def _exists_unit_of_measure(self, uom_id: uuid.UUID) -> bool:
        return (
            self._session.scalar(
                select(UnitOfMeasureModel.id)
                .where(UnitOfMeasureModel.id == uom_id)
                .limit(1)
            )
            is not None
        )

    def _resolve_supplier_alias_item_id(
        self,
        *,
        business_unit_id: uuid.UUID,
        supplier_id: uuid.UUID,
        source_item_name: str,
    ) -> uuid.UUID | None:
        alias = self._session.scalar(
            select(SupplierItemAliasModel)
            .where(SupplierItemAliasModel.business_unit_id == business_unit_id)
            .where(SupplierItemAliasModel.supplier_id == supplier_id)
            .where(
                SupplierItemAliasModel.source_item_key
                == self._normalize_alias_key(source_item_name)
            )
            .limit(1)
        )
        if alias is None or alias.status != "mapped":
            return None
        return alias.inventory_item_id

    def _upsert_supplier_aliases(
        self,
        *,
        draft: PurchaseInvoiceDraftModel,
        supplier_id: uuid.UUID | None,
        reviewed_lines: list[dict],
    ) -> None:
        if supplier_id is None:
            return

        now = datetime.now(UTC)
        for line in reviewed_lines:
            source_item_name = line.get("supplier_product_name")
            if not isinstance(source_item_name, str) or not source_item_name.strip():
                continue

            source_item_key = self._normalize_alias_key(source_item_name)
            alias = self._session.scalar(
                select(SupplierItemAliasModel)
                .where(SupplierItemAliasModel.business_unit_id == draft.business_unit_id)
                .where(SupplierItemAliasModel.supplier_id == supplier_id)
                .where(SupplierItemAliasModel.source_item_key == source_item_key)
                .limit(1)
            )
            inventory_item_id = self._parse_optional_uuid(line.get("inventory_item_id"))
            status = "mapped" if inventory_item_id is not None else "review_required"
            if alias is None:
                alias = SupplierItemAliasModel(
                    business_unit_id=draft.business_unit_id,
                    supplier_id=supplier_id,
                    inventory_item_id=inventory_item_id,
                    source_item_name=source_item_name.strip(),
                    source_item_key=source_item_key,
                    internal_display_name=line.get("description"),
                    status=status,
                    mapping_confidence="manual_review",
                    occurrence_count=1,
                    first_seen_at=now,
                    last_seen_at=now,
                )
                self._session.add(alias)
                continue

            alias.source_item_name = source_item_name.strip()
            alias.internal_display_name = line.get("description")
            alias.occurrence_count += 1
            alias.last_seen_at = now
            if inventory_item_id is not None:
                alias.inventory_item_id = inventory_item_id
                alias.status = "mapped"
                alias.mapping_confidence = "manual"
            elif alias.inventory_item_id is None:
                alias.status = "review_required"

    @staticmethod
    def _normalize_alias_key(value: str) -> str:
        return re.sub(r"\s+", " ", value.strip().casefold())

    @staticmethod
    def _parse_optional_uuid(value: object) -> uuid.UUID | None:
        if value is None or value == "":
            return None
        return uuid.UUID(str(value))

    @staticmethod
    def _decimal_to_string(
        value: Decimal | None,
        quant: Decimal = Decimal("0.01"),
    ) -> str | None:
        if value is None:
            return None
        return str(value.quantize(quant, rounding=ROUND_HALF_UP))
