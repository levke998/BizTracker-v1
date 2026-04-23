"""Inventory response schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class InventoryItemCreateRequest(BaseModel):
    """Create request for a new inventory item."""

    business_unit_id: uuid.UUID
    name: str = Field(min_length=1, max_length=150)
    item_type: str = Field(min_length=1, max_length=50)
    uom_id: uuid.UUID
    track_stock: bool
    is_active: bool = True


class InventoryItemUpdateRequest(BaseModel):
    """Update request for one inventory item."""

    name: str = Field(min_length=1, max_length=150)
    item_type: str = Field(min_length=1, max_length=50)
    uom_id: uuid.UUID
    track_stock: bool
    is_active: bool = True


class InventoryItemResponse(BaseModel):
    """Read model for one inventory item."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    business_unit_id: uuid.UUID
    name: str
    item_type: str
    uom_id: uuid.UUID
    track_stock: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime


InventoryMovementType = Literal["purchase", "adjustment", "waste", "initial_stock"]


class InventoryMovementCreateRequest(BaseModel):
    """Create request for one inventory movement log entry."""

    business_unit_id: uuid.UUID
    inventory_item_id: uuid.UUID
    movement_type: InventoryMovementType
    quantity: Decimal = Field(gt=0)
    uom_id: uuid.UUID
    unit_cost: Decimal | None = Field(default=None, gt=0)
    note: str | None = Field(default=None, max_length=500)
    occurred_at: datetime | None = None


class InventoryMovementResponse(BaseModel):
    """Read model for one inventory movement log entry."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    business_unit_id: uuid.UUID
    inventory_item_id: uuid.UUID
    movement_type: str
    quantity: Decimal
    uom_id: uuid.UUID
    unit_cost: Decimal | None
    note: str | None
    occurred_at: datetime
    created_at: datetime


class InventoryStockLevelResponse(BaseModel):
    """Read model for one aggregated actual stock level."""

    model_config = ConfigDict(from_attributes=True)

    inventory_item_id: uuid.UUID
    business_unit_id: uuid.UUID
    name: str
    item_type: str
    uom_id: uuid.UUID
    track_stock: bool
    is_active: bool
    current_quantity: Decimal
    last_movement_at: datetime | None
    movement_count: int


class InventoryTheoreticalStockResponse(BaseModel):
    """Read model for one theoretical stock row."""

    model_config = ConfigDict(from_attributes=True)

    inventory_item_id: uuid.UUID
    business_unit_id: uuid.UUID
    name: str
    item_type: str
    uom_id: uuid.UUID
    track_stock: bool
    is_active: bool
    actual_quantity: Decimal
    theoretical_quantity: Decimal | None
    variance_quantity: Decimal | None
    last_actual_movement_at: datetime | None
    last_estimated_event_at: datetime | None
    estimation_basis: str
