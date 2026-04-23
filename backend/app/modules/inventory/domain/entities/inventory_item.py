"""Inventory domain entities."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime


@dataclass(frozen=True, slots=True)
class InventoryItem:
    """Represents one inventory item read model."""

    id: uuid.UUID
    business_unit_id: uuid.UUID
    name: str
    item_type: str
    uom_id: uuid.UUID
    track_stock: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class NewInventoryItem:
    """Draft inventory item before persistence."""

    business_unit_id: uuid.UUID
    name: str
    item_type: str
    uom_id: uuid.UUID
    track_stock: bool
    is_active: bool


@dataclass(frozen=True, slots=True)
class InventoryMovement:
    """Represents one persisted inventory movement log entry."""

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


@dataclass(frozen=True, slots=True)
class NewInventoryMovement:
    """Draft inventory movement before persistence."""

    business_unit_id: uuid.UUID
    inventory_item_id: uuid.UUID
    movement_type: str
    quantity: Decimal
    uom_id: uuid.UUID
    unit_cost: Decimal | None
    note: str | None
    occurred_at: datetime


@dataclass(frozen=True, slots=True)
class InventoryStockLevel:
    """Aggregated actual stock level derived from movement logs."""

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


@dataclass(frozen=True, slots=True)
class InventoryTheoreticalStock:
    """Projected stock read model with explicit estimation readiness markers."""

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
