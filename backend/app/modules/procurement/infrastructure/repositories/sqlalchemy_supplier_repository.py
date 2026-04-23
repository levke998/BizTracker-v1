"""Procurement SQLAlchemy supplier repository."""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.master_data.infrastructure.orm.business_unit_model import (
    BusinessUnitModel,
)
from app.modules.procurement.domain.entities.supplier import NewSupplier, Supplier
from app.modules.procurement.infrastructure.orm.supplier_model import SupplierModel


class SqlAlchemySupplierRepository:
    """SQLAlchemy repository for procurement suppliers."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def list_many(
        self,
        *,
        business_unit_id: uuid.UUID | None = None,
        is_active: bool | None = None,
        limit: int = 50,
    ) -> list[Supplier]:
        statement = select(SupplierModel)

        if business_unit_id is not None:
            statement = statement.where(SupplierModel.business_unit_id == business_unit_id)
        if is_active is not None:
            statement = statement.where(SupplierModel.is_active == is_active)

        statement = statement.order_by(SupplierModel.name.asc()).limit(limit)
        models = self._session.scalars(statement).all()
        return [self._to_entity(model) for model in models]

    def create(self, supplier: NewSupplier) -> Supplier:
        model = SupplierModel(
            business_unit_id=supplier.business_unit_id,
            name=supplier.name,
            tax_id=supplier.tax_id,
            contact_name=supplier.contact_name,
            email=supplier.email,
            phone=supplier.phone,
            notes=supplier.notes,
            is_active=supplier.is_active,
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

    def exists_by_name(
        self,
        *,
        business_unit_id: uuid.UUID,
        name: str,
    ) -> bool:
        count = self._session.scalar(
            select(func.count())
            .select_from(SupplierModel)
            .where(SupplierModel.business_unit_id == business_unit_id)
            .where(SupplierModel.name == name)
        )
        return bool(count)

    @staticmethod
    def _to_entity(model: SupplierModel) -> Supplier:
        return Supplier(
            id=model.id,
            business_unit_id=model.business_unit_id,
            name=model.name,
            tax_id=model.tax_id,
            contact_name=model.contact_name,
            email=model.email,
            phone=model.phone,
            notes=model.notes,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
