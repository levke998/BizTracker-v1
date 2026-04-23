"""Inventory domain entities."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
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
