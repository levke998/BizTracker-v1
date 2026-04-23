"""SQLAlchemy category repository."""

from __future__ import annotations

import uuid

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.modules.master_data.domain.entities.category import Category
from app.modules.master_data.infrastructure.orm.category_model import CategoryModel


class SqlAlchemyCategoryRepository:
    """SQLAlchemy-backed category repository."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def list_by_business_unit(
        self,
        business_unit_id: uuid.UUID,
        *,
        active_only: bool = True,
    ) -> list[Category]:
        statement: Select[tuple[CategoryModel]] = (
            select(CategoryModel)
            .where(CategoryModel.business_unit_id == business_unit_id)
            .order_by(CategoryModel.name.asc())
        )
        if active_only:
            statement = statement.where(CategoryModel.is_active.is_(True))

        items = self._session.scalars(statement).all()
        return [self._to_entity(item) for item in items]

    @staticmethod
    def _to_entity(model: CategoryModel) -> Category:
        return Category(
            id=model.id,
            business_unit_id=model.business_unit_id,
            parent_id=model.parent_id,
            name=model.name,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
