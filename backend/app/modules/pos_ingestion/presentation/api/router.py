"""POS ingestion API boundary for external cash-register connectors."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.modules.demo_pos.application.commands.create_demo_receipt import (
    CreateDemoPosReceiptCommand,
    DemoPosBusinessUnitNotFoundError,
    DemoPosProductNotFoundError,
    DemoPosValidationError,
    NewDemoPosReceiptLine,
)
from app.modules.demo_pos.presentation.dependencies import (
    get_create_demo_pos_receipt_command,
)
from app.modules.demo_pos.presentation.schemas.demo_pos import (
    DemoPosReceiptRequest,
    DemoPosReceiptResponse,
)

router = APIRouter(prefix="/pos-ingestion", tags=["pos-ingestion"])


@router.post(
    "/receipts",
    response_model=DemoPosReceiptResponse,
    status_code=status.HTTP_201_CREATED,
)
def ingest_pos_receipt(
    payload: DemoPosReceiptRequest,
    command: Annotated[
        CreateDemoPosReceiptCommand,
        Depends(get_create_demo_pos_receipt_command),
    ],
) -> DemoPosReceiptResponse:
    """Ingest one normalized POS receipt from a demo or external connector."""

    try:
        receipt = command.execute(
            business_unit_id=payload.business_unit_id,
            payment_method=payload.payment_method,
            receipt_no=payload.receipt_no,
            occurred_at=payload.occurred_at,
            lines=[
                NewDemoPosReceiptLine(
                    product_id=line.product_id,
                    quantity=line.quantity,
                )
                for line in payload.lines
            ],
        )
    except DemoPosBusinessUnitNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except DemoPosProductNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except DemoPosValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    return DemoPosReceiptResponse.model_validate(receipt)
