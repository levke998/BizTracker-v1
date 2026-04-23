"""Inventory response schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class InventoryItemCreateRequest(BaseModel):
    """Create request for a new inventory item."""

    business_unit_id: uuid.UUID
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
