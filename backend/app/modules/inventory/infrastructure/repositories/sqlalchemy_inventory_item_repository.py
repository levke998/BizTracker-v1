"""Inventory SQLAlchemy repository."""

from __future__ import annotations

import uuid
from decimal import Decimal

import sqlalchemy as sa
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.inventory.domain.entities.inventory_item import (
    InventoryItem,
    InventoryMovement,
    InventoryStockLevel,
    NewInventoryItem,
    NewInventoryMovement,
)
from app.modules.inventory.infrastructure.orm.inventory_movement_model import (
    InventoryMovementModel,
)
from app.modules.inventory.infrastructure.orm.inventory_item_model import (
    InventoryItemModel,
)
from app.modules.master_data.infrastructure.orm.business_unit_model import (
    BusinessUnitModel,
)
from app.modules.master_data.infrastructure.orm.unit_of_measure_model import (
    UnitOfMeasureModel,
)


class SqlAlchemyInventoryItemRepository:
    """Read-side SQLAlchemy repository for inventory items."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def list_many(
        self,
        *,
        business_unit_id: uuid.UUID | None = None,
        item_type: str | None = None,
        limit: int = 50,
    ) -> list[InventoryItem]:
        statement = select(InventoryItemModel)

        if business_unit_id is not None:
            statement = statement.where(
                InventoryItemModel.business_unit_id == business_unit_id
            )
        if item_type is not None:
            statement = statement.where(InventoryItemModel.item_type == item_type)

        statement = statement.order_by(InventoryItemModel.name.asc()).limit(limit)
        models = self._session.scalars(statement).all()
        return [self._to_entity(model) for model in models]

    def create(self, item: NewInventoryItem) -> InventoryItem:
        model = InventoryItemModel(
            business_unit_id=item.business_unit_id,
            name=item.name,
            item_type=item.item_type,
            uom_id=item.uom_id,
            track_stock=item.track_stock,
            is_active=item.is_active,
        )
        self._session.add(model)
        self._session.commit()
        self._session.refresh(model)
        return self._to_entity(model)

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
        model = self._session.get(InventoryItemModel, inventory_item_id)
        if model is None:
            raise ValueError(f"Inventory item {inventory_item_id} was not found.")

        model.name = name
        model.item_type = item_type
        model.uom_id = uom_id
        model.track_stock = track_stock
        model.is_active = is_active

        self._session.commit()
        self._session.refresh(model)
        return self._to_entity(model)

    def archive(self, inventory_item_id: uuid.UUID) -> InventoryItem:
        model = self._session.get(InventoryItemModel, inventory_item_id)
        if model is None:
            raise ValueError(f"Inventory item {inventory_item_id} was not found.")

        model.is_active = False

        self._session.commit()
        self._session.refresh(model)
        return self._to_entity(model)

    def create_movement(self, movement: NewInventoryMovement) -> InventoryMovement:
        model = InventoryMovementModel(
            business_unit_id=movement.business_unit_id,
            inventory_item_id=movement.inventory_item_id,
            movement_type=movement.movement_type,
            quantity=movement.quantity,
            uom_id=movement.uom_id,
            unit_cost=movement.unit_cost,
            note=movement.note,
            source_type=movement.source_type,
            source_id=movement.source_id,
            occurred_at=movement.occurred_at,
        )
        self._session.add(model)
        self._session.commit()
        self._session.refresh(model)
        return self._to_movement_entity(model)

    def list_movements(
        self,
        *,
        business_unit_id: uuid.UUID | None = None,
        inventory_item_id: uuid.UUID | None = None,
        movement_type: str | None = None,
        limit: int = 50,
    ) -> list[InventoryMovement]:
        statement = select(InventoryMovementModel)

        if business_unit_id is not None:
            statement = statement.where(
                InventoryMovementModel.business_unit_id == business_unit_id
            )
        if inventory_item_id is not None:
            statement = statement.where(
                InventoryMovementModel.inventory_item_id == inventory_item_id
            )
        if movement_type is not None:
            statement = statement.where(
                InventoryMovementModel.movement_type == movement_type
            )

        statement = statement.order_by(
            InventoryMovementModel.occurred_at.desc(),
            InventoryMovementModel.created_at.desc(),
        ).limit(limit)

        models = self._session.scalars(statement).all()
        return [self._to_movement_entity(model) for model in models]

    def business_unit_exists(self, business_unit_id: uuid.UUID) -> bool:
        count = self._session.scalar(
            select(func.count())
            .select_from(BusinessUnitModel)
            .where(BusinessUnitModel.id == business_unit_id)
        )
        return bool(count)

    def unit_of_measure_exists(self, uom_id: uuid.UUID) -> bool:
        count = self._session.scalar(
            select(func.count())
            .select_from(UnitOfMeasureModel)
            .where(UnitOfMeasureModel.id == uom_id)
        )
        return bool(count)

    def exists_by_name(
        self,
        *,
        business_unit_id: uuid.UUID,
        name: str,
        exclude_inventory_item_id: uuid.UUID | None = None,
    ) -> bool:
        statement = (
            select(func.count())
            .select_from(InventoryItemModel)
            .where(InventoryItemModel.business_unit_id == business_unit_id)
            .where(InventoryItemModel.name == name)
        )
        if exclude_inventory_item_id is not None:
            statement = statement.where(InventoryItemModel.id != exclude_inventory_item_id)

        count = self._session.scalar(statement)
        return bool(count)

    def get_by_id(self, inventory_item_id: uuid.UUID) -> InventoryItem | None:
        model = self._session.get(InventoryItemModel, inventory_item_id)
        if model is None:
            return None
        return self._to_entity(model)

    def list_stock_levels(
        self,
        *,
        business_unit_id: uuid.UUID | None = None,
        inventory_item_id: uuid.UUID | None = None,
        item_type: str | None = None,
        limit: int = 50,
    ) -> list[InventoryStockLevel]:
        signed_quantity = sa.case(
            (
                InventoryMovementModel.movement_type.in_(
                    ["purchase", "initial_stock", "adjustment"]
                ),
                InventoryMovementModel.quantity,
            ),
            (InventoryMovementModel.movement_type == "waste", -InventoryMovementModel.quantity),
            else_=0,
        )

        statement = (
            select(
                InventoryItemModel.id.label("inventory_item_id"),
                InventoryItemModel.business_unit_id,
                InventoryItemModel.name,
                InventoryItemModel.item_type,
                InventoryItemModel.uom_id,
                InventoryItemModel.track_stock,
                InventoryItemModel.is_active,
                func.coalesce(func.sum(signed_quantity), 0).label("current_quantity"),
                func.max(InventoryMovementModel.occurred_at).label("last_movement_at"),
                func.count(InventoryMovementModel.id).label("movement_count"),
            )
            .select_from(InventoryItemModel)
            .outerjoin(
                InventoryMovementModel,
                InventoryMovementModel.inventory_item_id == InventoryItemModel.id,
            )
        )

        if business_unit_id is not None:
            statement = statement.where(
                InventoryItemModel.business_unit_id == business_unit_id
            )
        if inventory_item_id is not None:
            statement = statement.where(InventoryItemModel.id == inventory_item_id)
        if item_type is not None:
            statement = statement.where(InventoryItemModel.item_type == item_type)

        statement = (
            statement.group_by(
                InventoryItemModel.id,
                InventoryItemModel.business_unit_id,
                InventoryItemModel.name,
                InventoryItemModel.item_type,
                InventoryItemModel.uom_id,
                InventoryItemModel.track_stock,
                InventoryItemModel.is_active,
            )
            .order_by(InventoryItemModel.name.asc())
            .limit(limit)
        )

        rows = self._session.execute(statement).all()
        return [
            InventoryStockLevel(
                inventory_item_id=row.inventory_item_id,
                business_unit_id=row.business_unit_id,
                name=row.name,
                item_type=row.item_type,
                uom_id=row.uom_id,
                track_stock=row.track_stock,
                is_active=row.is_active,
                current_quantity=Decimal(row.current_quantity),
                last_movement_at=row.last_movement_at,
                movement_count=row.movement_count,
            )
            for row in rows
        ]

    @staticmethod
    def _to_entity(model: InventoryItemModel) -> InventoryItem:
        return InventoryItem(
            id=model.id,
            business_unit_id=model.business_unit_id,
            name=model.name,
            item_type=model.item_type,
            uom_id=model.uom_id,
            track_stock=model.track_stock,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def _to_movement_entity(model: InventoryMovementModel) -> InventoryMovement:
        unit_cost = None
        if model.unit_cost is not None:
            unit_cost = Decimal(model.unit_cost)

        return InventoryMovement(
            id=model.id,
            business_unit_id=model.business_unit_id,
            inventory_item_id=model.inventory_item_id,
            movement_type=model.movement_type,
            quantity=Decimal(model.quantity),
            uom_id=model.uom_id,
            unit_cost=unit_cost,
            note=model.note,
            source_type=model.source_type,
            source_id=model.source_id,
            occurred_at=model.occurred_at,
            created_at=model.created_at,
        )
