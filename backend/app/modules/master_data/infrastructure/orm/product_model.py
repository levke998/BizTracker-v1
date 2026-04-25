"""Product ORM model."""

from __future__ import annotations

from typing import TYPE_CHECKING
from decimal import Decimal
import uuid

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.modules.master_data.infrastructure.orm.business_unit_model import (
        BusinessUnitModel,
    )
    from app.modules.master_data.infrastructure.orm.category_model import CategoryModel


class ProductModel(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Sellable or business-tracked product."""

    __tablename__ = "product"
    __table_args__ = (
        sa.Index("ix_core_product_business_unit_id", "business_unit_id"),
        sa.Index("ix_core_product_category_id", "category_id"),
        sa.Index("ix_core_product_sku", "sku"),
        sa.Index("ix_core_product_business_unit_name", "business_unit_id", "name"),
        {"schema": "core"},
    )

    business_unit_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid(as_uuid=True),
        sa.ForeignKey("core.business_unit.id", ondelete="RESTRICT"),
        nullable=False,
    )
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        sa.Uuid(as_uuid=True),
        sa.ForeignKey("core.category.id", ondelete="SET NULL"),
        nullable=True,
    )
    sales_uom_id: Mapped[uuid.UUID | None] = mapped_column(
        sa.Uuid(as_uuid=True),
        sa.ForeignKey("core.unit_of_measure.id", ondelete="RESTRICT"),
        nullable=True,
    )
    sku: Mapped[str | None] = mapped_column(sa.String(64), nullable=True)
    name: Mapped[str] = mapped_column(sa.String(200), nullable=False)
    product_type: Mapped[str] = mapped_column(sa.String(50), nullable=False)
    sale_price_gross: Mapped[Decimal | None] = mapped_column(
        sa.Numeric(12, 2),
        nullable=True,
    )
    default_unit_cost: Mapped[Decimal | None] = mapped_column(
        sa.Numeric(12, 2),
        nullable=True,
    )
    currency: Mapped[str] = mapped_column(
        sa.String(3),
        nullable=False,
        server_default=sa.text("'HUF'"),
    )
    is_active: Mapped[bool] = mapped_column(
        sa.Boolean,
        nullable=False,
        server_default=sa.text("true"),
    )

    business_unit: Mapped["BusinessUnitModel"] = relationship(back_populates="products")
    category: Mapped["CategoryModel | None"] = relationship(back_populates="products")
