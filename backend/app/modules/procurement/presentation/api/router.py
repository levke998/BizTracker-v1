"""Procurement API router."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

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
)
from app.modules.procurement.application.commands.create_supplier import (
    CreateSupplierCommand,
    ProcurementBusinessUnitNotFoundError,
    SupplierAlreadyExistsError,
)
from app.modules.procurement.application.queries.list_purchase_invoices import (
    ListPurchaseInvoicesQuery,
)
from app.modules.procurement.application.queries.list_suppliers import ListSuppliersQuery
from app.modules.procurement.presentation.dependencies import (
    get_create_purchase_invoice_command,
    get_create_supplier_command,
    get_list_purchase_invoices_query,
    get_list_suppliers_query,
)
from app.modules.procurement.presentation.schemas.purchase_invoice import (
    PurchaseInvoiceCreateRequest,
    PurchaseInvoiceResponse,
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
                )
                for line in payload.lines
            ),
        )
    except (
        ProcurementInvoiceBusinessUnitNotFoundError,
        ProcurementInvoiceSupplierNotFoundError,
        ProcurementInvoiceUnitOfMeasureNotFoundError,
        ProcurementInvoiceInventoryItemNotFoundError,
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
