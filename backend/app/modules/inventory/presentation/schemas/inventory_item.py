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
InventoryCorrectionReason = Literal[
    "physical_count",
    "waste",
    "breakage",
    "spoilage",
    "theft_suspected",
    "recipe_error",
    "mapping_error",
    "missing_purchase_invoice",
    "other",
]


class InventoryMovementCreateRequest(BaseModel):
    """Create request for one inventory movement log entry."""

    business_unit_id: uuid.UUID
    inventory_item_id: uuid.UUID
    movement_type: InventoryMovementType
    quantity: Decimal = Field(gt=0)
    uom_id: uuid.UUID
    unit_cost: Decimal | None = Field(default=None, gt=0)
    reason_code: InventoryCorrectionReason | None = None
    note: str | None = Field(default=None, max_length=500)
    occurred_at: datetime | None = None


class PhysicalStockCountCreateRequest(BaseModel):
    """Request for one physical stock count correction."""

    business_unit_id: uuid.UUID
    inventory_item_id: uuid.UUID
    counted_quantity: Decimal = Field(ge=0)
    uom_id: uuid.UUID
    reason_code: InventoryCorrectionReason = "physical_count"
    note: str | None = Field(default=None, max_length=500)
    occurred_at: datetime | None = None


class PhysicalStockCountResponse(BaseModel):
    """Result of one physical stock count correction."""

    model_config = ConfigDict(from_attributes=True)

    inventory_item_id: uuid.UUID
    business_unit_id: uuid.UUID
    previous_quantity: Decimal
    counted_quantity: Decimal
    adjustment_quantity: Decimal
    movement: "InventoryMovementResponse"


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
    reason_code: str | None
    note: str | None
    source_type: str | None
    source_id: uuid.UUID | None
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
    default_unit_cost: Decimal | None
    actual_stock_value: Decimal | None
    theoretical_stock_value: Decimal | None
    variance_stock_value: Decimal | None
    variance_status: str
    last_actual_movement_at: datetime | None
    last_estimated_event_at: datetime | None
    estimation_basis: str


class InventoryVarianceReasonSummaryResponse(BaseModel):
    """Read model for correction movement totals grouped by reason."""

    model_config = ConfigDict(from_attributes=True)

    reason_code: str
    movement_count: int
    total_quantity: Decimal
    net_quantity_delta: Decimal
    latest_occurred_at: datetime | None


class InventoryVarianceTrendPointResponse(BaseModel):
    """Read model for daily correction movement totals."""

    model_config = ConfigDict(from_attributes=True)

    bucket_date: datetime
    movement_count: int
    shortage_quantity: Decimal
    surplus_quantity: Decimal
    net_quantity_delta: Decimal
    estimated_shortage_value: Decimal
    estimated_surplus_value: Decimal
    estimated_net_value_delta: Decimal
    missing_cost_movement_count: int


class InventoryVarianceItemSummaryResponse(BaseModel):
    """Read model for correction totals grouped by item."""

    model_config = ConfigDict(from_attributes=True)

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


class InventoryVariancePeriodComparisonResponse(BaseModel):
    """Read model for current vs previous variance period controlling."""

    model_config = ConfigDict(from_attributes=True)

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


class InventoryVarianceThresholdUpdateRequest(BaseModel):
    """Update request for business-unit inventory variance thresholds."""

    business_unit_id: uuid.UUID
    high_loss_value_threshold: Decimal = Field(ge=0)
    worsening_percent_threshold: Decimal = Field(ge=0)


class InventoryVarianceThresholdResponse(BaseModel):
    """Effective inventory variance threshold response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID | None
    business_unit_id: uuid.UUID
    high_loss_value_threshold: Decimal
    worsening_percent_threshold: Decimal
    is_default: bool
    created_at: datetime | None
    updated_at: datetime | None


class EstimatedConsumptionAuditResponse(BaseModel):
    """Read model for one estimated consumption audit row."""

    model_config = ConfigDict(from_attributes=True)

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
