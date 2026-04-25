"""SQLAlchemy product repository."""

from __future__ import annotations

import uuid

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.modules.master_data.domain.entities.product import Product
from app.modules.master_data.infrastructure.orm.product_model import ProductModel


class SqlAlchemyProductRepository:
    """SQLAlchemy-backed product repository."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def list_by_business_unit(
        self,
        business_unit_id: uuid.UUID,
        *,
        active_only: bool = True,
    ) -> list[Product]:
        statement: Select[tuple[ProductModel]] = (
            select(ProductModel)
            .where(ProductModel.business_unit_id == business_unit_id)
            .order_by(ProductModel.name.asc())
        )
        if active_only:
            statement = statement.where(ProductModel.is_active.is_(True))

        items = self._session.scalars(statement).all()
        return [self._to_entity(item) for item in items]

    @staticmethod
    def _to_entity(model: ProductModel) -> Product:
        return Product(
            id=model.id,
            business_unit_id=model.business_unit_id,
            category_id=model.category_id,
            sales_uom_id=model.sales_uom_id,
            sku=model.sku,
            name=model.name,
            product_type=model.product_type,
            sale_price_gross=model.sale_price_gross,
            default_unit_cost=model.default_unit_cost,
            currency=model.currency,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
