"""Inventory read API routes."""

from __future__ import annotations

import uuid
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
from app.modules.inventory.application.commands.create_inventory_item import (
    CreateInventoryItemCommand,
    InventoryBusinessUnitNotFoundError,
    InventoryItemAlreadyExistsError,
    InventoryUnitOfMeasureNotFoundError,
)
from app.modules.inventory.application.queries.list_inventory_items import (
    ListInventoryItemsQuery,
)
from app.modules.inventory.application.queries.list_stock_levels import (
    ListInventoryStockLevelsQuery,
)
from app.modules.inventory.presentation.dependencies import (
    get_create_inventory_movement_command,
    get_create_inventory_item_command,
    get_list_inventory_items_query,
    get_list_inventory_stock_levels_query,
)
from app.modules.inventory.presentation.schemas.inventory_item import (
    InventoryMovementCreateRequest,
    InventoryMovementResponse,
    InventoryItemCreateRequest,
    InventoryItemResponse,
    InventoryStockLevelResponse,
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
