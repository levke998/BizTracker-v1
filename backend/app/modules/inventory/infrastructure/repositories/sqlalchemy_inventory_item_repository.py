"""Inventory SQLAlchemy repository."""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.inventory.domain.entities.inventory_item import (
    InventoryItem,
    NewInventoryItem,
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
    ) -> bool:
        count = self._session.scalar(
            select(func.count())
            .select_from(InventoryItemModel)
            .where(InventoryItemModel.business_unit_id == business_unit_id)
            .where(InventoryItemModel.name == name)
        )
        return bool(count)

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
