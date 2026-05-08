"""Inventory read API routes."""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi import HTTPException, status

from app.modules.inventory.application.commands.create_inventory_movement import (
    CreateInventoryMovementCommand,
    InventoryMovementBusinessUnitMismatchError,
    InventoryMovementBusinessUnitNotFoundError,
    InventoryMovementInventoryItemNotFoundError,
    InventoryMovementUnitCostRequiredError,
    InventoryMovementUnitOfMeasureMismatchError,
    InventoryMovementUnitOfMeasureNotFoundError,
)
from app.modules.inventory.application.commands.register_physical_stock_count import (
    PhysicalStockCountBusinessUnitMismatchError,
    PhysicalStockCountBusinessUnitNotFoundError,
    PhysicalStockCountInventoryItemNotFoundError,
    PhysicalStockCountUnitOfMeasureMismatchError,
    PhysicalStockCountUnitOfMeasureNotFoundError,
    RegisterPhysicalStockCountCommand,
)
from app.modules.inventory.application.commands.archive_inventory_item import (
    ArchiveInventoryItemCommand,
)
from app.modules.inventory.application.commands.create_inventory_item import (
    CreateInventoryItemCommand,
    InventoryBusinessUnitNotFoundError,
    InventoryItemAlreadyExistsError,
    InventoryUnitOfMeasureNotFoundError,
)
from app.modules.inventory.application.commands.update_inventory_item import (
    InventoryItemNotFoundError,
    UpdateInventoryItemCommand,
)
from app.modules.inventory.application.commands.upsert_variance_threshold import (
    InventoryVarianceThresholdBusinessUnitNotFoundError,
    UpsertInventoryVarianceThresholdCommand,
)
from app.modules.inventory.application.queries.list_inventory_items import (
    ListInventoryItemsQuery,
)
from app.modules.inventory.application.queries.get_variance_period_comparison import (
    GetInventoryVariancePeriodComparisonQuery,
)
from app.modules.inventory.application.queries.get_variance_threshold import (
    GetInventoryVarianceThresholdQuery,
)
from app.modules.inventory.application.queries.list_estimated_consumption import (
    ListEstimatedConsumptionAuditQuery,
)
from app.modules.inventory.application.queries.list_inventory_movements import (
    ListInventoryMovementsQuery,
)
from app.modules.inventory.application.queries.list_stock_levels import (
    ListInventoryStockLevelsQuery,
)
from app.modules.inventory.application.queries.list_theoretical_stock import (
    ListInventoryTheoreticalStockQuery,
)
from app.modules.inventory.application.queries.list_variance_reason_summary import (
    ListInventoryVarianceReasonSummaryQuery,
)
from app.modules.inventory.application.queries.list_variance_trend import (
    ListInventoryVarianceTrendQuery,
)
from app.modules.inventory.application.queries.list_variance_item_summary import (
    ListInventoryVarianceItemSummaryQuery,
)
from app.modules.inventory.presentation.dependencies import (
    get_archive_inventory_item_command,
    get_create_inventory_movement_command,
    get_create_inventory_item_command,
    get_inventory_variance_period_comparison_query,
    get_inventory_variance_threshold_query,
    get_list_inventory_items_query,
    get_list_estimated_consumption_audit_query,
    get_list_inventory_movements_query,
    get_list_inventory_stock_levels_query,
    get_list_inventory_theoretical_stock_query,
    get_list_inventory_variance_item_summary_query,
    get_list_inventory_variance_reason_summary_query,
    get_list_inventory_variance_trend_query,
    get_register_physical_stock_count_command,
    get_update_inventory_item_command,
    get_upsert_inventory_variance_threshold_command,
)
from app.modules.inventory.presentation.schemas.inventory_item import (
    InventoryMovementCreateRequest,
    InventoryMovementResponse,
    EstimatedConsumptionAuditResponse,
    InventoryItemCreateRequest,
    InventoryItemResponse,
    InventoryItemUpdateRequest,
    InventoryStockLevelResponse,
    InventoryTheoreticalStockResponse,
    InventoryVarianceItemSummaryResponse,
    InventoryVariancePeriodComparisonResponse,
    InventoryVarianceReasonSummaryResponse,
    InventoryVarianceThresholdResponse,
    InventoryVarianceThresholdUpdateRequest,
    InventoryVarianceTrendPointResponse,
    PhysicalStockCountCreateRequest,
    PhysicalStockCountResponse,
)

router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.post(
    "/movements",
    response_model=InventoryMovementResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_inventory_movement(
    payload: InventoryMovementCreateRequest,
    command: Annotated[
        CreateInventoryMovementCommand,
        Depends(get_create_inventory_movement_command),
    ],
) -> InventoryMovementResponse:
    """Create one inventory movement log entry."""

    try:
        movement = command.execute(
            business_unit_id=payload.business_unit_id,
            inventory_item_id=payload.inventory_item_id,
            movement_type=payload.movement_type,
            quantity=payload.quantity,
            uom_id=payload.uom_id,
            unit_cost=payload.unit_cost,
            occurred_at=payload.occurred_at,
            reason_code=payload.reason_code,
            note=payload.note,
        )
    except (
        InventoryMovementBusinessUnitNotFoundError,
        InventoryMovementInventoryItemNotFoundError,
        InventoryMovementUnitOfMeasureNotFoundError,
    ) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except (
        InventoryMovementBusinessUnitMismatchError,
        InventoryMovementUnitOfMeasureMismatchError,
        InventoryMovementUnitCostRequiredError,
    ) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc

    return InventoryMovementResponse.model_validate(movement)


@router.post(
    "/physical-stock-counts",
    response_model=PhysicalStockCountResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_physical_stock_count(
    payload: PhysicalStockCountCreateRequest,
    command: Annotated[
        RegisterPhysicalStockCountCommand,
        Depends(get_register_physical_stock_count_command),
    ],
) -> PhysicalStockCountResponse:
    """Register a physical stock count and create the needed correction movement."""

    try:
        result = command.execute(
            business_unit_id=payload.business_unit_id,
            inventory_item_id=payload.inventory_item_id,
            counted_quantity=payload.counted_quantity,
            uom_id=payload.uom_id,
            reason_code=payload.reason_code,
            occurred_at=payload.occurred_at,
            note=payload.note,
        )
    except (
        PhysicalStockCountBusinessUnitNotFoundError,
        PhysicalStockCountInventoryItemNotFoundError,
        PhysicalStockCountUnitOfMeasureNotFoundError,
    ) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except (
        PhysicalStockCountBusinessUnitMismatchError,
        PhysicalStockCountUnitOfMeasureMismatchError,
    ) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc

    return PhysicalStockCountResponse.model_validate(result)


@router.get("/movements", response_model=list[InventoryMovementResponse])
def list_inventory_movements(
    query: Annotated[
        ListInventoryMovementsQuery,
        Depends(get_list_inventory_movements_query),
    ],
    business_unit_id: uuid.UUID | None = Query(default=None),
    inventory_item_id: uuid.UUID | None = Query(default=None),
    movement_type: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[InventoryMovementResponse]:
    """Return inventory movement log entries with lightweight filters."""

    items = query.execute(
        business_unit_id=business_unit_id,
        inventory_item_id=inventory_item_id,
        movement_type=movement_type,
        limit=limit,
    )
    return [InventoryMovementResponse.model_validate(item) for item in items]


@router.get(
    "/variance-reasons",
    response_model=list[InventoryVarianceReasonSummaryResponse],
)
def list_inventory_variance_reasons(
    query: Annotated[
        ListInventoryVarianceReasonSummaryQuery,
        Depends(get_list_inventory_variance_reason_summary_query),
    ],
    business_unit_id: uuid.UUID | None = Query(default=None),
    inventory_item_id: uuid.UUID | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
) -> list[InventoryVarianceReasonSummaryResponse]:
    """Return correction movement totals grouped by user-facing reason code."""

    items = query.execute(
        business_unit_id=business_unit_id,
        inventory_item_id=inventory_item_id,
        limit=limit,
    )
    return [InventoryVarianceReasonSummaryResponse.model_validate(item) for item in items]


@router.get(
    "/variance-trend",
    response_model=list[InventoryVarianceTrendPointResponse],
)
def list_inventory_variance_trend(
    query: Annotated[
        ListInventoryVarianceTrendQuery,
        Depends(get_list_inventory_variance_trend_query),
    ],
    business_unit_id: uuid.UUID | None = Query(default=None),
    inventory_item_id: uuid.UUID | None = Query(default=None),
    days: int = Query(default=30, ge=1, le=365),
) -> list[InventoryVarianceTrendPointResponse]:
    """Return daily correction movement totals for inventory controlling."""

    items = query.execute(
        business_unit_id=business_unit_id,
        inventory_item_id=inventory_item_id,
        days=days,
    )
    return [InventoryVarianceTrendPointResponse.model_validate(item) for item in items]


@router.get(
    "/variance-items",
    response_model=list[InventoryVarianceItemSummaryResponse],
)
def list_inventory_variance_items(
    query: Annotated[
        ListInventoryVarianceItemSummaryQuery,
        Depends(get_list_inventory_variance_item_summary_query),
    ],
    business_unit_id: uuid.UUID | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
) -> list[InventoryVarianceItemSummaryResponse]:
    """Return correction totals grouped by inventory item."""

    items = query.execute(
        business_unit_id=business_unit_id,
        limit=limit,
    )
    return [InventoryVarianceItemSummaryResponse.model_validate(item) for item in items]


@router.get(
    "/variance-period-comparison",
    response_model=InventoryVariancePeriodComparisonResponse,
)
def get_inventory_variance_period_comparison(
    query: Annotated[
        GetInventoryVariancePeriodComparisonQuery,
        Depends(get_inventory_variance_period_comparison_query),
    ],
    business_unit_id: uuid.UUID | None = Query(default=None),
    inventory_item_id: uuid.UUID | None = Query(default=None),
    days: int = Query(default=30, ge=1, le=365),
    high_loss_value_threshold: Decimal | None = Query(default=None, ge=0),
    worsening_percent_threshold: Decimal | None = Query(default=None, ge=0),
) -> InventoryVariancePeriodComparisonResponse:
    """Compare current inventory variance period to the previous same-length period."""

    item = query.execute(
        business_unit_id=business_unit_id,
        inventory_item_id=inventory_item_id,
        days=days,
        high_loss_value_threshold=high_loss_value_threshold,
        worsening_percent_threshold=worsening_percent_threshold,
    )
    return InventoryVariancePeriodComparisonResponse.model_validate(item)


@router.get(
    "/variance-thresholds",
    response_model=InventoryVarianceThresholdResponse,
)
def get_inventory_variance_threshold(
    query: Annotated[
        GetInventoryVarianceThresholdQuery,
        Depends(get_inventory_variance_threshold_query),
    ],
    business_unit_id: uuid.UUID = Query(),
) -> InventoryVarianceThresholdResponse:
    """Return effective inventory variance thresholds for one business unit."""

    item = query.execute(business_unit_id=business_unit_id)
    return InventoryVarianceThresholdResponse.model_validate(item)


@router.put(
    "/variance-thresholds",
    response_model=InventoryVarianceThresholdResponse,
)
def upsert_inventory_variance_threshold(
    payload: InventoryVarianceThresholdUpdateRequest,
    command: Annotated[
        UpsertInventoryVarianceThresholdCommand,
        Depends(get_upsert_inventory_variance_threshold_command),
    ],
) -> InventoryVarianceThresholdResponse:
    """Create or update inventory variance thresholds for one business unit."""

    try:
        item = command.execute(
            business_unit_id=payload.business_unit_id,
            high_loss_value_threshold=payload.high_loss_value_threshold,
            worsening_percent_threshold=payload.worsening_percent_threshold,
        )
    except InventoryVarianceThresholdBusinessUnitNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return InventoryVarianceThresholdResponse.model_validate(item)


@router.post(
    "/items",
    response_model=InventoryItemResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_inventory_item(
    payload: InventoryItemCreateRequest,
    command: Annotated[CreateInventoryItemCommand, Depends(get_create_inventory_item_command)],
) -> InventoryItemResponse:
    """Create a new inventory item."""

    try:
        item = command.execute(
            business_unit_id=payload.business_unit_id,
            name=payload.name,
            item_type=payload.item_type,
            uom_id=payload.uom_id,
            track_stock=payload.track_stock,
            is_active=payload.is_active,
        )
    except InventoryBusinessUnitNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except InventoryUnitOfMeasureNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except InventoryItemAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    return InventoryItemResponse.model_validate(item)


@router.patch("/items/{inventory_item_id}", response_model=InventoryItemResponse)
def update_inventory_item(
    inventory_item_id: uuid.UUID,
    payload: InventoryItemUpdateRequest,
    command: Annotated[UpdateInventoryItemCommand, Depends(get_update_inventory_item_command)],
) -> InventoryItemResponse:
    """Update one inventory item."""

    try:
        item = command.execute(
            inventory_item_id=inventory_item_id,
            name=payload.name,
            item_type=payload.item_type,
            uom_id=payload.uom_id,
            track_stock=payload.track_stock,
            is_active=payload.is_active,
        )
    except InventoryItemNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except InventoryUnitOfMeasureNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except InventoryItemAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    return InventoryItemResponse.model_validate(item)


@router.delete("/items/{inventory_item_id}", response_model=InventoryItemResponse)
def archive_inventory_item(
    inventory_item_id: uuid.UUID,
    command: Annotated[
        ArchiveInventoryItemCommand,
        Depends(get_archive_inventory_item_command),
    ],
) -> InventoryItemResponse:
    """Archive one inventory item by marking it inactive."""

    try:
        item = command.execute(inventory_item_id=inventory_item_id)
    except InventoryItemNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return InventoryItemResponse.model_validate(item)


@router.get("/items", response_model=list[InventoryItemResponse])
def list_inventory_items(
    query: Annotated[ListInventoryItemsQuery, Depends(get_list_inventory_items_query)],
    business_unit_id: uuid.UUID | None = Query(default=None),
    item_type: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[InventoryItemResponse]:
    """Return inventory items with minimal filters."""

    items = query.execute(
        business_unit_id=business_unit_id,
        item_type=item_type,
        limit=limit,
    )
    return [InventoryItemResponse.model_validate(item) for item in items]


@router.get("/stock-levels", response_model=list[InventoryStockLevelResponse])
def list_inventory_stock_levels(
    query: Annotated[
        ListInventoryStockLevelsQuery,
        Depends(get_list_inventory_stock_levels_query),
    ],
    business_unit_id: uuid.UUID | None = Query(default=None),
    inventory_item_id: uuid.UUID | None = Query(default=None),
    item_type: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[InventoryStockLevelResponse]:
    """Return aggregated actual stock levels from inventory movements."""

    items = query.execute(
        business_unit_id=business_unit_id,
        inventory_item_id=inventory_item_id,
        item_type=item_type,
        limit=limit,
    )
    return [InventoryStockLevelResponse.model_validate(item) for item in items]


@router.get(
    "/estimated-consumption",
    response_model=list[EstimatedConsumptionAuditResponse],
)
def list_estimated_consumption_audit(
    query: Annotated[
        ListEstimatedConsumptionAuditQuery,
        Depends(get_list_estimated_consumption_audit_query),
    ],
    business_unit_id: uuid.UUID | None = Query(default=None),
    inventory_item_id: uuid.UUID | None = Query(default=None),
    product_id: uuid.UUID | None = Query(default=None),
    source_type: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[EstimatedConsumptionAuditResponse]:
    """Return estimated stock decrease audit rows created from POS sales."""

    items = query.execute(
        business_unit_id=business_unit_id,
        inventory_item_id=inventory_item_id,
        product_id=product_id,
        source_type=source_type,
        limit=limit,
    )
    return [EstimatedConsumptionAuditResponse.model_validate(item) for item in items]


@router.get(
    "/theoretical-stock",
    response_model=list[InventoryTheoreticalStockResponse],
)
def list_inventory_theoretical_stock(
    query: Annotated[
        ListInventoryTheoreticalStockQuery,
        Depends(get_list_inventory_theoretical_stock_query),
    ],
    business_unit_id: uuid.UUID | None = Query(default=None),
    inventory_item_id: uuid.UUID | None = Query(default=None),
    item_type: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[InventoryTheoreticalStockResponse]:
    """Return the first theoretical-stock read model with explicit readiness markers."""

    items = query.execute(
        business_unit_id=business_unit_id,
        inventory_item_id=inventory_item_id,
        item_type=item_type,
        limit=limit,
    )
    return [InventoryTheoreticalStockResponse.model_validate(item) for item in items]
