"""Business unit ORM model."""

from __future__ import annotations

from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.modules.master_data.infrastructure.orm.category_model import CategoryModel
    from app.modules.master_data.infrastructure.orm.location_model import LocationModel
    from app.modules.master_data.infrastructure.orm.product_model import ProductModel


class BusinessUnitModel(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Top-level business unit such as Gourmand or Flow."""

    __tablename__ = "business_unit"
    __table_args__ = (
        sa.UniqueConstraint("code", name="uq_core_business_unit_code"),
        sa.Index("ix_core_business_unit_code", "code"),
        {"schema": "core"},
    )

    code: Mapped[str] = mapped_column(sa.String(50), nullable=False)
    name: Mapped[str] = mapped_column(sa.String(150), nullable=False)
    type: Mapped[str] = mapped_column(sa.String(50), nullable=False)
    is_active: Mapped[bool] = mapped_column(
        sa.Boolean,
        nullable=False,
        server_default=sa.text("true"),
    )

    locations: Mapped[list["LocationModel"]] = relationship(back_populates="business_unit")
    categories: Mapped[list["CategoryModel"]] = relationship(
        back_populates="business_unit"
    )
    products: Mapped[list["ProductModel"]] = relationship(back_populates="business_unit")
