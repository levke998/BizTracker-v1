"""Procurement API router."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status

from app.modules.procurement.application.commands.create_purchase_invoice import (
    CreatePurchaseInvoiceCommand,
    CreatePurchaseInvoiceLineInput,
    ProcurementInvoiceAlreadyExistsError,
    ProcurementInvoiceBusinessUnitNotFoundError,
    ProcurementInvoiceInventoryItemMismatchError,
    ProcurementInvoiceInventoryItemNotFoundError,
    ProcurementInvoiceInventoryItemUnitMismatchError,
    ProcurementInvoiceSupplierMismatchError,
    ProcurementInvoiceSupplierNotFoundError,
    ProcurementInvoiceUnitOfMeasureNotFoundError,
    ProcurementInvoiceVatRateNotFoundError,
)
from app.modules.procurement.application.commands.create_purchase_invoice_from_pdf_review import (
    CreatePurchaseInvoiceFromPdfReviewCommand,
    PurchaseInvoicePdfReviewAlreadyConvertedError,
    PurchaseInvoicePdfReviewDraftNotFoundError,
    PurchaseInvoicePdfReviewIncompleteError,
    PurchaseInvoicePdfReviewNotReadyError,
)
from app.modules.procurement.application.commands.post_purchase_invoice import (
    PostPurchaseInvoiceCommand,
    PurchaseInvoiceAlreadyPostedError,
    PurchaseInvoiceNotFoundError,
)
from app.modules.procurement.application.commands.upload_purchase_invoice_pdf_draft import (
    PurchaseInvoiceDraftBusinessUnitNotFoundError,
    PurchaseInvoiceDraftSupplierMismatchError,
    PurchaseInvoiceDraftValidationError,
    UploadPurchaseInvoicePdfDraftCommand,
)
from app.modules.procurement.application.commands.update_purchase_invoice_pdf_review import (
    PurchaseInvoicePdfDraftNotFoundError,
    PurchaseInvoicePdfReviewInput,
    PurchaseInvoicePdfReviewInventoryItemMismatchError,
    PurchaseInvoicePdfReviewLineInput,
    PurchaseInvoicePdfReviewSupplierMismatchError,
    PurchaseInvoicePdfReviewUnitOfMeasureNotFoundError,
    PurchaseInvoicePdfReviewVatRateNotFoundError,
    UpdatePurchaseInvoicePdfReviewCommand,
)
from app.modules.procurement.application.commands.create_supplier import (
    CreateSupplierCommand,
    ProcurementBusinessUnitNotFoundError,
    SupplierAlreadyExistsError,
)
from app.modules.procurement.application.queries.list_purchase_invoices import (
    ListPurchaseInvoicesQuery,
)
from app.modules.procurement.application.queries.list_purchase_invoice_pdf_drafts import (
    ListPurchaseInvoicePdfDraftsQuery,
)
from app.modules.procurement.application.queries.list_suppliers import ListSuppliersQuery
from app.modules.procurement.application.services.supplier_item_alias_mapping import (
    SupplierItemAliasInventoryItemMismatchError,
    SupplierItemAliasMappingService,
    SupplierItemAliasNotFoundError,
)
from app.modules.procurement.presentation.dependencies import (
    get_create_purchase_invoice_command,
    get_create_purchase_invoice_from_pdf_review_command,
    get_create_supplier_command,
    get_list_purchase_invoices_query,
    get_list_purchase_invoice_pdf_drafts_query,
    get_list_suppliers_query,
    get_post_purchase_invoice_command,
    get_supplier_item_alias_mapping_service,
    get_update_purchase_invoice_pdf_review_command,
    get_upload_purchase_invoice_pdf_draft_command,
)
from app.modules.procurement.presentation.schemas.purchase_invoice import (
    PurchaseInvoiceCreateRequest,
    PurchaseInvoicePdfDraftResponse,
    PurchaseInvoicePdfReviewRequest,
    PurchaseInvoicePostingResponse,
    PurchaseInvoiceResponse,
    SupplierItemAliasMappingRequest,
    SupplierItemAliasResponse,
)
from app.modules.procurement.presentation.schemas.supplier import (
    SupplierCreateRequest,
    SupplierResponse,
)

router = APIRouter(prefix="/procurement", tags=["procurement"])


@router.post(
    "/suppliers",
    response_model=SupplierResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_supplier(
    payload: SupplierCreateRequest,
    command: Annotated[CreateSupplierCommand, Depends(get_create_supplier_command)],
) -> SupplierResponse:
    """Create one procurement supplier."""

    try:
        supplier = command.execute(
            business_unit_id=payload.business_unit_id,
            name=payload.name,
            tax_id=payload.tax_id,
            contact_name=payload.contact_name,
            email=payload.email,
            phone=payload.phone,
            notes=payload.notes,
            is_active=payload.is_active,
        )
    except ProcurementBusinessUnitNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except SupplierAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    return SupplierResponse.model_validate(supplier)


@router.get("/suppliers", response_model=list[SupplierResponse])
def list_suppliers(
    query: Annotated[ListSuppliersQuery, Depends(get_list_suppliers_query)],
    business_unit_id: uuid.UUID | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[SupplierResponse]:
    """Return suppliers with lightweight filters."""

    items = query.execute(
        business_unit_id=business_unit_id,
        is_active=is_active,
        limit=limit,
    )
    return [SupplierResponse.model_validate(item) for item in items]


@router.post(
    "/purchase-invoices",
    response_model=PurchaseInvoiceResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_purchase_invoice(
    payload: PurchaseInvoiceCreateRequest,
    command: Annotated[
        CreatePurchaseInvoiceCommand,
        Depends(get_create_purchase_invoice_command),
    ],
) -> PurchaseInvoiceResponse:
    """Create one manual purchase invoice with its line items."""

    try:
        invoice = command.execute(
            business_unit_id=payload.business_unit_id,
            supplier_id=payload.supplier_id,
            invoice_number=payload.invoice_number,
            invoice_date=payload.invoice_date,
            currency=payload.currency,
            gross_total=payload.gross_total,
            notes=payload.notes,
            lines=tuple(
                CreatePurchaseInvoiceLineInput(
                    inventory_item_id=line.inventory_item_id,
                    description=line.description,
                    quantity=line.quantity,
                    uom_id=line.uom_id,
                    unit_net_amount=line.unit_net_amount,
                    line_net_amount=line.line_net_amount,
                    vat_rate_id=line.vat_rate_id,
                    vat_amount=line.vat_amount,
                    line_gross_amount=line.line_gross_amount,
                )
                for line in payload.lines
            ),
        )
    except (
        ProcurementInvoiceBusinessUnitNotFoundError,
        ProcurementInvoiceSupplierNotFoundError,
        ProcurementInvoiceUnitOfMeasureNotFoundError,
        ProcurementInvoiceInventoryItemNotFoundError,
        ProcurementInvoiceVatRateNotFoundError,
    ) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ProcurementInvoiceAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except (
        ProcurementInvoiceSupplierMismatchError,
        ProcurementInvoiceInventoryItemMismatchError,
        ProcurementInvoiceInventoryItemUnitMismatchError,
    ) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc

    return PurchaseInvoiceResponse.model_validate(invoice)


@router.post(
    "/purchase-invoices/{purchase_invoice_id}/post",
    response_model=PurchaseInvoicePostingResponse,
)
def post_purchase_invoice(
    purchase_invoice_id: uuid.UUID,
    command: Annotated[
        PostPurchaseInvoiceCommand,
        Depends(get_post_purchase_invoice_command),
    ],
) -> PurchaseInvoicePostingResponse:
    """Post one purchase invoice into finance and actual inventory movements."""

    try:
        result = command.execute(purchase_invoice_id=purchase_invoice_id)
    except PurchaseInvoiceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except PurchaseInvoiceAlreadyPostedError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    return PurchaseInvoicePostingResponse.model_validate(result)


@router.get("/purchase-invoices", response_model=list[PurchaseInvoiceResponse])
def list_purchase_invoices(
    query: Annotated[
        ListPurchaseInvoicesQuery,
        Depends(get_list_purchase_invoices_query),
    ],
    business_unit_id: uuid.UUID | None = Query(default=None),
    supplier_id: uuid.UUID | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[PurchaseInvoiceResponse]:
    """Return purchase invoices with lightweight filters."""

    items = query.execute(
        business_unit_id=business_unit_id,
        supplier_id=supplier_id,
        limit=limit,
    )
    return [PurchaseInvoiceResponse.model_validate(item) for item in items]


@router.post(
    "/purchase-invoice-drafts/pdf",
    response_model=PurchaseInvoicePdfDraftResponse,
    status_code=status.HTTP_201_CREATED,
)
def upload_purchase_invoice_pdf_draft(
    business_unit_id: Annotated[uuid.UUID, Form(...)],
    file: Annotated[UploadFile, File(...)],
    command: Annotated[
        UploadPurchaseInvoicePdfDraftCommand,
        Depends(get_upload_purchase_invoice_pdf_draft_command),
    ],
    supplier_id: Annotated[uuid.UUID | None, Form()] = None,
) -> PurchaseInvoicePdfDraftResponse:
    """Upload one supplier invoice PDF as a review-required draft."""

    try:
        draft = command.execute(
            business_unit_id=business_unit_id,
            supplier_id=supplier_id,
            upload=file,
        )
    except PurchaseInvoiceDraftBusinessUnitNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except PurchaseInvoiceDraftSupplierMismatchError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc
    except PurchaseInvoiceDraftValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc

    return PurchaseInvoicePdfDraftResponse.model_validate(draft)


@router.get(
    "/purchase-invoice-drafts",
    response_model=list[PurchaseInvoicePdfDraftResponse],
)
def list_purchase_invoice_pdf_drafts(
    query: Annotated[
        ListPurchaseInvoicePdfDraftsQuery,
        Depends(get_list_purchase_invoice_pdf_drafts_query),
    ],
    business_unit_id: uuid.UUID | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[PurchaseInvoicePdfDraftResponse]:
    """Return uploaded supplier invoice PDF drafts."""

    drafts = query.execute(business_unit_id=business_unit_id, limit=limit)
    return [PurchaseInvoicePdfDraftResponse.model_validate(draft) for draft in drafts]


@router.put(
    "/purchase-invoice-drafts/{draft_id}/review",
    response_model=PurchaseInvoicePdfDraftResponse,
)
def update_purchase_invoice_pdf_review(
    draft_id: uuid.UUID,
    payload: PurchaseInvoicePdfReviewRequest,
    command: Annotated[
        UpdatePurchaseInvoicePdfReviewCommand,
        Depends(get_update_purchase_invoice_pdf_review_command),
    ],
) -> PurchaseInvoicePdfDraftResponse:
    """Save reviewed PDF invoice fields and calculated VAT line values."""

    try:
        draft = command.execute(
            draft_id=draft_id,
            review=PurchaseInvoicePdfReviewInput(
                supplier_id=payload.supplier_id,
                invoice_number=payload.invoice_number,
                invoice_date=payload.invoice_date,
                currency=payload.currency,
                gross_total=payload.gross_total,
                notes=payload.notes,
                lines=tuple(
                    PurchaseInvoicePdfReviewLineInput(
                        description=line.description,
                        supplier_product_name=line.supplier_product_name,
                        inventory_item_id=line.inventory_item_id,
                        quantity=line.quantity,
                        uom_id=line.uom_id,
                        vat_rate_id=line.vat_rate_id,
                        unit_net_amount=line.unit_net_amount,
                        line_net_amount=line.line_net_amount,
                        vat_amount=line.vat_amount,
                        line_gross_amount=line.line_gross_amount,
                        notes=line.notes,
                    )
                    for line in payload.lines
                ),
            ),
        )
    except PurchaseInvoicePdfDraftNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except (
        PurchaseInvoicePdfReviewUnitOfMeasureNotFoundError,
        PurchaseInvoicePdfReviewVatRateNotFoundError,
    ) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except (
        PurchaseInvoicePdfReviewSupplierMismatchError,
        PurchaseInvoicePdfReviewInventoryItemMismatchError,
    ) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc

    return PurchaseInvoicePdfDraftResponse.model_validate(draft)


@router.post(
    "/purchase-invoice-drafts/{draft_id}/create-purchase-invoice",
    response_model=PurchaseInvoiceResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_purchase_invoice_from_pdf_review(
    draft_id: uuid.UUID,
    command: Annotated[
        CreatePurchaseInvoiceFromPdfReviewCommand,
        Depends(get_create_purchase_invoice_from_pdf_review_command),
    ],
) -> PurchaseInvoiceResponse:
    """Create a final purchase invoice from a review-ready PDF draft."""

    try:
        invoice = command.execute(draft_id=draft_id)
    except PurchaseInvoicePdfReviewDraftNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except (
        ProcurementInvoiceSupplierNotFoundError,
        ProcurementInvoiceUnitOfMeasureNotFoundError,
        ProcurementInvoiceInventoryItemNotFoundError,
        ProcurementInvoiceVatRateNotFoundError,
    ) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except (
        PurchaseInvoicePdfReviewAlreadyConvertedError,
        ProcurementInvoiceAlreadyExistsError,
    ) as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except (
        PurchaseInvoicePdfReviewNotReadyError,
        PurchaseInvoicePdfReviewIncompleteError,
        ProcurementInvoiceSupplierMismatchError,
        ProcurementInvoiceInventoryItemMismatchError,
        ProcurementInvoiceInventoryItemUnitMismatchError,
    ) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc

    return PurchaseInvoiceResponse.model_validate(invoice)


@router.get(
    "/supplier-item-aliases",
    response_model=list[SupplierItemAliasResponse],
)
def list_supplier_item_aliases(
    service: Annotated[
        SupplierItemAliasMappingService,
        Depends(get_supplier_item_alias_mapping_service),
    ],
    business_unit_id: uuid.UUID | None = Query(default=None),
    supplier_id: uuid.UUID | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=100, ge=1, le=500),
) -> list[SupplierItemAliasResponse]:
    """Return supplier invoice item aliases for review screens."""

    aliases = service.list_aliases(
        business_unit_id=business_unit_id,
        supplier_id=supplier_id,
        status=status_filter,
        limit=limit,
    )
    return [SupplierItemAliasResponse.model_validate(alias) for alias in aliases]


@router.patch(
    "/supplier-item-aliases/{alias_id}/mapping",
    response_model=SupplierItemAliasResponse,
)
def approve_supplier_item_alias_mapping(
    alias_id: uuid.UUID,
    payload: SupplierItemAliasMappingRequest,
    service: Annotated[
        SupplierItemAliasMappingService,
        Depends(get_supplier_item_alias_mapping_service),
    ],
) -> SupplierItemAliasResponse:
    """Approve one supplier item alias against an internal inventory item."""

    try:
        alias = service.approve_mapping(
            alias_id=alias_id,
            inventory_item_id=payload.inventory_item_id,
            internal_display_name=payload.internal_display_name,
            notes=payload.notes,
        )
    except SupplierItemAliasNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except SupplierItemAliasInventoryItemMismatchError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc

    return SupplierItemAliasResponse.model_validate(alias)
