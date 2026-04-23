"""SQLAlchemy location repository."""

from __future__ import annotations

import uuid

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.modules.master_data.domain.entities.location import Location
from app.modules.master_data.infrastructure.orm.location_model import LocationModel


class SqlAlchemyLocationRepository:
    """SQLAlchemy-backed location repository."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def list_by_business_unit(
        self,
        business_unit_id: uuid.UUID,
        *,
        active_only: bool = True,
    ) -> list[Location]:
        statement: Select[tuple[LocationModel]] = (
            select(LocationModel)
            .where(LocationModel.business_unit_id == business_unit_id)
            .order_by(LocationModel.name.asc())
        )
        if active_only:
            statement = statement.where(LocationModel.is_active.is_(True))

        items = self._session.scalars(statement).all()
        return [self._to_entity(item) for item in items]

    @staticmethod
    def _to_entity(model: LocationModel) -> Location:
        return Location(
            id=model.id,
            business_unit_id=model.business_unit_id,
            name=model.name,
            kind=model.kind,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
