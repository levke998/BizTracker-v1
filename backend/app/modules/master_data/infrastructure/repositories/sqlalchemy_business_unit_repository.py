"""SQLAlchemy business unit repository."""

from __future__ import annotations

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.modules.master_data.domain.entities.business_unit import BusinessUnit
from app.modules.master_data.infrastructure.orm.business_unit_model import (
    BusinessUnitModel,
)


class SqlAlchemyBusinessUnitRepository:
    """SQLAlchemy-backed business unit repository."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def list_all(self, *, active_only: bool = True) -> list[BusinessUnit]:
        statement: Select[tuple[BusinessUnitModel]] = select(BusinessUnitModel).order_by(
            BusinessUnitModel.name.asc()
        )
        if active_only:
            statement = statement.where(BusinessUnitModel.is_active.is_(True))

        items = self._session.scalars(statement).all()
        return [self._to_entity(item) for item in items]

    @staticmethod
    def _to_entity(model: BusinessUnitModel) -> BusinessUnit:
        return BusinessUnit(
            id=model.id,
            code=model.code,
            name=model.name,
            type=model.type,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
