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
    reason_code: str | None
    note: str | None
    source_type: str | None
    source_id: uuid.UUID | None
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
    reason_code: str | None
    note: str | None
    source_type: str | None
    source_id: uuid.UUID | None
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
    default_unit_cost: Decimal | None
    estimated_stock_quantity: Decimal | None
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
    default_unit_cost: Decimal | None
    actual_stock_value: Decimal | None
    theoretical_stock_value: Decimal | None
    variance_stock_value: Decimal | None
    variance_status: str
    last_actual_movement_at: datetime | None
    last_estimated_event_at: datetime | None
    estimation_basis: str


@dataclass(frozen=True, slots=True)
class InventoryVarianceReasonSummary:
    """Aggregated correction movement summary grouped by variance reason."""

    reason_code: str
    movement_count: int
    total_quantity: Decimal
    net_quantity_delta: Decimal
    latest_occurred_at: datetime | None


@dataclass(frozen=True, slots=True)
class InventoryVarianceTrendPoint:
    """Daily correction movement totals for inventory controlling."""

    bucket_date: datetime
    movement_count: int
    shortage_quantity: Decimal
    surplus_quantity: Decimal
    net_quantity_delta: Decimal
    estimated_shortage_value: Decimal
    estimated_surplus_value: Decimal
    estimated_net_value_delta: Decimal
    missing_cost_movement_count: int


@dataclass(frozen=True, slots=True)
class InventoryVarianceItemSummary:
    """Correction totals grouped by inventory item."""

    inventory_item_id: uuid.UUID
    name: str
    item_type: str
    default_unit_cost: Decimal | None
    movement_count: int
    shortage_quantity: Decimal
    surplus_quantity: Decimal
    net_quantity_delta: Decimal
    estimated_shortage_value: Decimal | None
    estimated_surplus_value: Decimal | None
    estimated_net_value_delta: Decimal | None
    missing_cost_movement_count: int
    anomaly_status: str
    latest_occurred_at: datetime | None


@dataclass(frozen=True, slots=True)
class InventoryVariancePeriodComparison:
    """Current period vs previous period comparison for inventory controlling."""

    current_start_at: datetime
    current_end_at: datetime
    previous_start_at: datetime
    previous_end_at: datetime
    period_days: int
    current_movement_count: int
    previous_movement_count: int
    movement_count_change: int
    current_shortage_quantity: Decimal
    previous_shortage_quantity: Decimal
    shortage_quantity_change: Decimal
    current_estimated_shortage_value: Decimal
    previous_estimated_shortage_value: Decimal
    estimated_shortage_value_change: Decimal
    estimated_shortage_value_change_percent: Decimal | None
    current_missing_cost_movement_count: int
    previous_missing_cost_movement_count: int
    decision_status: str
    recommendation: str


@dataclass(frozen=True, slots=True)
class InventoryVarianceThreshold:
    """Effective inventory controlling thresholds for one business unit."""

    id: uuid.UUID | None
    business_unit_id: uuid.UUID
    high_loss_value_threshold: Decimal
    worsening_percent_threshold: Decimal
    is_default: bool
    created_at: datetime | None
    updated_at: datetime | None


@dataclass(frozen=True, slots=True)
class EstimatedConsumptionAudit:
    """Explains one estimated stock decrease from a POS sale source row."""

    id: uuid.UUID
    business_unit_id: uuid.UUID
    product_id: uuid.UUID
    product_name: str
    inventory_item_id: uuid.UUID
    inventory_item_name: str
    recipe_version_id: uuid.UUID | None
    source_type: str
    source_id: uuid.UUID
    source_dedupe_key: str | None
    receipt_no: str | None
    estimation_basis: str
    quantity: Decimal
    uom_id: uuid.UUID
    uom_code: str
    quantity_before: Decimal
    quantity_after: Decimal
    occurred_at: datetime
    created_at: datetime
