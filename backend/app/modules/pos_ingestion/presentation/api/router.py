"""POS ingestion API boundary for external cash-register connectors."""

from __future__ import annotations

from datetime import datetime
import uuid
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.db.session import SessionLocal, get_db_session
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
from app.modules.pos_ingestion.application.services.pos_product_alias_mapping import (
    PosProductAliasMappingService,
    PosProductAliasNotFoundError,
    PosProductAliasProductMismatchError,
)
from app.modules.pos_ingestion.application.services.pos_missing_recipe_worklist import (
    PosMissingRecipeWorklistService,
)
from app.modules.weather.application.commands.backfill_weather import BackfillWeatherCommand
from app.modules.weather.application.commands.ensure_shared_weather_interval_coverage import (
    EnsureSharedWeatherIntervalCoverageCommand,
)
from app.modules.weather.application.services.weather_provider import WeatherProvider
from app.modules.weather.infrastructure.repositories.sqlalchemy_weather_repository import (
    SqlAlchemyWeatherRepository,
)
from app.modules.weather.presentation.dependencies import (
    get_weather_provider,
)

router = APIRouter(prefix="/pos-ingestion", tags=["pos-ingestion"])

DbSession = Annotated[Session, Depends(get_db_session)]


class PosProductAliasResponse(BaseModel):
    """One POS source product mapping/quarantine row."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    business_unit_id: uuid.UUID
    product_id: uuid.UUID | None
    source_system: str
    source_product_key: str
    source_product_name: str
    source_sku: str | None
    source_barcode: str | None
    status: str
    mapping_confidence: str
    occurrence_count: int
    first_seen_at: datetime | None
    last_seen_at: datetime | None
    last_import_batch_id: uuid.UUID | None
    last_import_row_id: uuid.UUID | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class PosMissingRecipeWorklistResponse(BaseModel):
    """One POS-origin product that still needs recipe setup."""

    model_config = ConfigDict(from_attributes=True)

    product_id: uuid.UUID
    business_unit_id: uuid.UUID
    product_name: str
    category_name: str | None
    product_type: str
    sale_price_gross: str | None
    sale_price_last_seen_at: datetime | None
    sale_price_source: str | None
    alias_count: int
    occurrence_count: int
    first_seen_at: datetime | None
    last_seen_at: datetime | None
    latest_source_product_name: str | None
    latest_source_system: str | None


def get_pos_product_alias_mapping_service(
    session: DbSession,
) -> PosProductAliasMappingService:
    """Wire POS alias review operations."""

    return PosProductAliasMappingService(session)


def get_pos_missing_recipe_worklist_service(
    session: DbSession,
) -> PosMissingRecipeWorklistService:
    """Wire POS missing-recipe worklist queries."""

    return PosMissingRecipeWorklistService(session)


class ApprovePosProductAliasRequest(BaseModel):
    """Approve one POS alias against an internal catalog product."""

    product_id: uuid.UUID
    notes: str | None = None


@router.get("/product-aliases", response_model=list[PosProductAliasResponse])
def list_pos_product_aliases(
    service: Annotated[
        PosProductAliasMappingService,
        Depends(get_pos_product_alias_mapping_service),
    ],
    business_unit_id: uuid.UUID | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
) -> list[PosProductAliasResponse]:
    """Return POS source product aliases for mapping review screens."""

    aliases = service.list_aliases(
        business_unit_id=business_unit_id,
        status=status_filter,
    )
    return [PosProductAliasResponse.model_validate(alias) for alias in aliases]


@router.get(
    "/products/missing-recipes",
    response_model=list[PosMissingRecipeWorklistResponse],
)
def list_pos_products_missing_recipes(
    service: Annotated[
        PosMissingRecipeWorklistService,
        Depends(get_pos_missing_recipe_worklist_service),
    ],
    business_unit_id: uuid.UUID | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
) -> list[PosMissingRecipeWorklistResponse]:
    """Return POS-origin products that do not have an active recipe yet."""

    items = service.list_items(
        business_unit_id=business_unit_id,
        limit=limit,
    )
    return [
        PosMissingRecipeWorklistResponse(
            product_id=item.product_id,
            business_unit_id=item.business_unit_id,
            product_name=item.product_name,
            category_name=item.category_name,
            product_type=item.product_type,
            sale_price_gross=(
                str(item.sale_price_gross) if item.sale_price_gross is not None else None
            ),
            sale_price_last_seen_at=item.sale_price_last_seen_at,
            sale_price_source=item.sale_price_source,
            alias_count=item.alias_count,
            occurrence_count=item.occurrence_count,
            first_seen_at=item.first_seen_at,
            last_seen_at=item.last_seen_at,
            latest_source_product_name=item.latest_source_product_name,
            latest_source_system=item.latest_source_system,
        )
        for item in items
    ]


@router.patch(
    "/product-aliases/{alias_id}/mapping",
    response_model=PosProductAliasResponse,
)
def approve_pos_product_alias_mapping(
    alias_id: uuid.UUID,
    payload: ApprovePosProductAliasRequest,
    service: Annotated[
        PosProductAliasMappingService,
        Depends(get_pos_product_alias_mapping_service),
    ],
) -> PosProductAliasResponse:
    """Approve a POS source product alias against one internal product."""

    try:
        alias = service.approve_mapping(
            alias_id=alias_id,
            product_id=payload.product_id,
            notes=payload.notes,
        )
    except PosProductAliasNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except PosProductAliasProductMismatchError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    return PosProductAliasResponse.model_validate(alias)


@router.post(
    "/receipts",
    response_model=DemoPosReceiptResponse,
    status_code=status.HTTP_201_CREATED,
)
def ingest_pos_receipt(
    payload: DemoPosReceiptRequest,
    background_tasks: BackgroundTasks,
    command: Annotated[
        CreateDemoPosReceiptCommand,
        Depends(get_create_demo_pos_receipt_command),
    ],
    weather_provider: Annotated[
        WeatherProvider,
        Depends(get_weather_provider),
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

    background_tasks.add_task(
        _ensure_receipt_weather_coverage,
        receipt.occurred_at,
        weather_provider,
    )
    return DemoPosReceiptResponse.model_validate(receipt)


def _ensure_receipt_weather_coverage(
    occurred_at: datetime,
    provider: WeatherProvider,
) -> None:
    """Best-effort weather preparation for live POS receipts."""

    session = SessionLocal()
    try:
        repository = SqlAlchemyWeatherRepository(session)
        backfill_command = BackfillWeatherCommand(repository=repository, provider=provider)
        command = EnsureSharedWeatherIntervalCoverageCommand(
            repository=repository,
            backfill_command=backfill_command,
        )
        command.execute(start_at=occurred_at, end_at=occurred_at)
    except Exception:
        return
    finally:
        session.close()
