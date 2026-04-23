"""Category ORM model."""

from __future__ import annotations

from typing import TYPE_CHECKING
import uuid

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.modules.master_data.infrastructure.orm.business_unit_model import (
        BusinessUnitModel,
    )
    from app.modules.master_data.infrastructure.orm.product_model import ProductModel


class CategoryModel(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Business-unit-specific category tree."""

    __tablename__ = "category"
    __table_args__ = (
        sa.Index("ix_core_category_business_unit_id", "business_unit_id"),
        sa.Index("ix_core_category_parent_id", "parent_id"),
        sa.Index(
            "ix_core_category_business_unit_parent_name",
            "business_unit_id",
            "parent_id",
            "name",
        ),
        {"schema": "core"},
    )

    business_unit_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid(as_uuid=True),
        sa.ForeignKey("core.business_unit.id", ondelete="RESTRICT"),
        nullable=False,
    )
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        sa.Uuid(as_uuid=True),
        sa.ForeignKey("core.category.id", ondelete="SET NULL"),
        nullable=True,
    )
    name: Mapped[str] = mapped_column(sa.String(150), nullable=False)
    is_active: Mapped[bool] = mapped_column(
        sa.Boolean,
        nullable=False,
        server_default=sa.text("true"),
    )

    business_unit: Mapped["BusinessUnitModel"] = relationship(
        back_populates="categories"
    )
    parent: Mapped["CategoryModel | None"] = relationship(
        back_populates="children",
        remote_side="CategoryModel.id",
    )
    children: Mapped[list["CategoryModel"]] = relationship(back_populates="parent")
    products: Mapped[list["ProductModel"]] = relationship(back_populates="category")
