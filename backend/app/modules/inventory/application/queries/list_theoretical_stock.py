"""Inventory theoretical stock list query."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from decimal import Decimal

from app.modules.inventory.domain.entities.inventory_item import (
    InventoryTheoreticalStock,
)
from app.modules.inventory.domain.repositories.inventory_item_repository import (
    InventoryItemRepository,
)

THEORETICAL_STOCK_ESTIMATION_BASIS = "not_configured"
RECIPE_THEORETICAL_STOCK_ESTIMATION_BASIS = "recipe_or_direct_pos"


@dataclass(slots=True)
class ListInventoryTheoreticalStockQuery:
    """Return an explicit theoretical-stock read model without mixing it with actual stock."""

    repository: InventoryItemRepository

    def execute(
        self,
        *,
        business_unit_id: uuid.UUID | None = None,
        inventory_item_id: uuid.UUID | None = None,
        item_type: str | None = None,
        limit: int = 50,
    ) -> list[InventoryTheoreticalStock]:
        stock_levels = self.repository.list_stock_levels(
            business_unit_id=business_unit_id,
            inventory_item_id=inventory_item_id,
            item_type=item_type,
            limit=limit,
        )

        estimated_events = {
            item.inventory_item_id: self.repository.list_estimated_consumption(
                business_unit_id=item.business_unit_id,
                inventory_item_id=item.inventory_item_id,
                limit=1,
            )
            for item in stock_levels
        }

        results: list[InventoryTheoreticalStock] = []
        for item in stock_levels:
            theoretical_quantity = item.estimated_stock_quantity
            variance_quantity = None
            if theoretical_quantity is not None:
                variance_quantity = (
                    item.current_quantity - theoretical_quantity
                ).quantize(Decimal("0.001"))

            default_unit_cost = item.default_unit_cost
            actual_stock_value = _value(item.current_quantity, default_unit_cost)
            theoretical_stock_value = _value(theoretical_quantity, default_unit_cost)
            variance_stock_value = _value(variance_quantity, default_unit_cost)
            estimate_rows = estimated_events.get(item.inventory_item_id, [])
            last_estimated_event_at = estimate_rows[0].occurred_at if estimate_rows else None

            results.append(
                InventoryTheoreticalStock(
                    inventory_item_id=item.inventory_item_id,
                    business_unit_id=item.business_unit_id,
                    name=item.name,
                    item_type=item.item_type,
                    uom_id=item.uom_id,
                    track_stock=item.track_stock,
                    is_active=item.is_active,
                    actual_quantity=item.current_quantity,
                    theoretical_quantity=theoretical_quantity,
                    variance_quantity=variance_quantity,
                    default_unit_cost=default_unit_cost,
                    actual_stock_value=actual_stock_value,
                    theoretical_stock_value=theoretical_stock_value,
                    variance_stock_value=variance_stock_value,
                    variance_status=_variance_status(
                        theoretical_quantity=theoretical_quantity,
                        variance_quantity=variance_quantity,
                        default_unit_cost=default_unit_cost,
                    ),
                    last_actual_movement_at=item.last_movement_at,
                    last_estimated_event_at=last_estimated_event_at,
                    estimation_basis=(
                        RECIPE_THEORETICAL_STOCK_ESTIMATION_BASIS
                        if theoretical_quantity is not None
                        else THEORETICAL_STOCK_ESTIMATION_BASIS
                    ),
                )
            )
        return results


def _value(
    quantity: Decimal | None,
    unit_cost: Decimal | None,
) -> Decimal | None:
    if quantity is None or unit_cost is None:
        return None
    return (quantity * unit_cost).quantize(Decimal("0.01"))


def _variance_status(
    *,
    theoretical_quantity: Decimal | None,
    variance_quantity: Decimal | None,
    default_unit_cost: Decimal | None,
) -> str:
    if theoretical_quantity is None:
        return "missing_theoretical_stock"
    if default_unit_cost is None:
        return "missing_cost"
    if variance_quantity is None or variance_quantity == 0:
        return "ok"
    if variance_quantity < 0:
        return "shortage_risk"
    return "surplus_or_unreviewed"
