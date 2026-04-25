"""Demo POS API routes."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db_session
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
    DemoPosCatalogProductResponse,
    DemoPosReceiptRequest,
    DemoPosReceiptResponse,
)
from app.modules.master_data.infrastructure.orm.category_model import CategoryModel
from app.modules.master_data.infrastructure.orm.product_model import ProductModel
from app.modules.master_data.infrastructure.orm.unit_of_measure_model import (
    UnitOfMeasureModel,
)

router = APIRouter(prefix="/demo-pos", tags=["demo-pos"])


@dataclass(frozen=True, slots=True)
class DemoPosCatalogProduct:
    """Projection for the demo POS product catalog."""

    id: uuid.UUID
    business_unit_id: uuid.UUID
    category_id: uuid.UUID | None
    category_name: str | None
    sales_uom_id: uuid.UUID | None
    sales_uom_code: str | None
    sales_uom_symbol: str | None
    sku: str | None
    name: str
    product_type: str
    sale_price_gross: Decimal
    default_unit_cost: Decimal | None
    currency: str


@router.get("/catalog", response_model=list[DemoPosCatalogProductResponse])
def list_demo_pos_catalog(
    business_unit_id: uuid.UUID,
    session: Annotated[Session, Depends(get_db_session)],
    product_type: str | None = Query(default=None),
) -> list[DemoPosCatalogProductResponse]:
    """Return active, priced products that can be sold by the demo POS."""

    statement = (
        select(ProductModel, CategoryModel.name, UnitOfMeasureModel.code, UnitOfMeasureModel.symbol)
        .outerjoin(CategoryModel, ProductModel.category_id == CategoryModel.id)
        .outerjoin(UnitOfMeasureModel, ProductModel.sales_uom_id == UnitOfMeasureModel.id)
        .where(ProductModel.business_unit_id == business_unit_id)
        .where(ProductModel.is_active.is_(True))
        .where(ProductModel.sale_price_gross.is_not(None))
        .order_by(CategoryModel.name.asc().nulls_last(), ProductModel.name.asc())
    )
    if product_type is not None:
        statement = statement.where(ProductModel.product_type == product_type)

    rows = session.execute(statement).all()
    return [
        DemoPosCatalogProductResponse.model_validate(
            DemoPosCatalogProduct(
                id=product.id,
                business_unit_id=product.business_unit_id,
                category_id=product.category_id,
                category_name=category_name,
                sales_uom_id=product.sales_uom_id,
                sales_uom_code=sales_uom_code,
                sales_uom_symbol=sales_uom_symbol,
                sku=product.sku,
                name=product.name,
                product_type=product.product_type,
                sale_price_gross=product.sale_price_gross,
                default_unit_cost=product.default_unit_cost,
                currency=product.currency,
            )
        )
        for product, category_name, sales_uom_code, sales_uom_symbol in rows
    ]


@router.post(
    "/receipts",
    response_model=DemoPosReceiptResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_demo_pos_receipt(
    payload: DemoPosReceiptRequest,
    command: Annotated[
        CreateDemoPosReceiptCommand,
        Depends(get_create_demo_pos_receipt_command),
    ],
) -> DemoPosReceiptResponse:
    """Accept one demo POS receipt and push it into the business data pipeline."""

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
