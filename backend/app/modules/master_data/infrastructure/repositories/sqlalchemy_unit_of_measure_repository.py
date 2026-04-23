"""SQLAlchemy unit-of-measure repository."""

from __future__ import annotations

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.modules.master_data.domain.entities.unit_of_measure import UnitOfMeasure
from app.modules.master_data.infrastructure.orm.unit_of_measure_model import (
    UnitOfMeasureModel,
)


class SqlAlchemyUnitOfMeasureRepository:
    """SQLAlchemy-backed unit-of-measure repository."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def list_all(self) -> list[UnitOfMeasure]:
        statement: Select[tuple[UnitOfMeasureModel]] = select(
            UnitOfMeasureModel
        ).order_by(UnitOfMeasureModel.name.asc())
        items = self._session.scalars(statement).all()
        return [self._to_entity(item) for item in items]

    @staticmethod
    def _to_entity(model: UnitOfMeasureModel) -> UnitOfMeasure:
        return UnitOfMeasure(
            id=model.id,
            code=model.code,
            name=model.name,
            symbol=model.symbol,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
