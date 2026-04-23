"""Inventory repository contract."""

from __future__ import annotations

import uuid
from typing import Protocol

from app.modules.inventory.domain.entities.inventory_item import (
    InventoryItem,
    InventoryMovement,
    InventoryStockLevel,
    NewInventoryItem,
    NewInventoryMovement,
)


class InventoryItemRepository(Protocol):
    """Defines persistence access for inventory item reads."""

    def list_many(
        self,
        *,
        business_unit_id: uuid.UUID | None = None,
        item_type: str | None = None,
        limit: int = 50,
    ) -> list[InventoryItem]:
        """List inventory items with lightweight filters."""

    def create(self, item: NewInventoryItem) -> InventoryItem:
        """Create one inventory item."""

    def update(
        self,
        *,
        inventory_item_id: uuid.UUID,
        name: str,
        item_type: str,
        uom_id: uuid.UUID,
        track_stock: bool,
        is_active: bool,
    ) -> InventoryItem:
        """Update one inventory item."""

    def archive(self, inventory_item_id: uuid.UUID) -> InventoryItem:
        """Archive one inventory item by setting it inactive."""

    def create_movement(self, movement: NewInventoryMovement) -> InventoryMovement:
        """Create one inventory movement log entry."""

    def list_movements(
        self,
        *,
        business_unit_id: uuid.UUID | None = None,
        inventory_item_id: uuid.UUID | None = None,
        movement_type: str | None = None,
        limit: int = 50,
    ) -> list[InventoryMovement]:
        """List inventory movement log entries with lightweight filters."""

    def business_unit_exists(self, business_unit_id: uuid.UUID) -> bool:
        """Return whether the referenced business unit exists."""

    def unit_of_measure_exists(self, uom_id: uuid.UUID) -> bool:
        """Return whether the referenced unit of measure exists."""

    def exists_by_name(
        self,
        *,
        business_unit_id: uuid.UUID,
        name: str,
        exclude_inventory_item_id: uuid.UUID | None = None,
    ) -> bool:
        """Return whether an item with the same name already exists in the business unit."""

    def get_by_id(self, inventory_item_id: uuid.UUID) -> InventoryItem | None:
        """Return one inventory item by its identifier when present."""

    def list_stock_levels(
        self,
        *,
        business_unit_id: uuid.UUID | None = None,
        inventory_item_id: uuid.UUID | None = None,
        item_type: str | None = None,
        limit: int = 50,
    ) -> list[InventoryStockLevel]:
        """Return aggregated actual stock levels from movement logs."""
