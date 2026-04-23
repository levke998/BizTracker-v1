"""Inventory item ORM model."""

from __future__ import annotations

import uuid

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class InventoryItemModel(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Read/write storage model for inventory master data."""

    __tablename__ = "inventory_item"
    __table_args__ = (
        sa.UniqueConstraint(
            "business_unit_id",
            "name",
            name="uq_core_inventory_item_business_unit_name",
        ),
        sa.Index("ix_core_inventory_item_business_unit_id", "business_unit_id"),
        sa.Index("ix_core_inventory_item_item_type", "item_type"),
        sa.Index("ix_core_inventory_item_name", "name"),
        {"schema": "core"},
    )

    business_unit_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid(as_uuid=True),
        sa.ForeignKey("core.business_unit.id", ondelete="RESTRICT"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(sa.String(150), nullable=False)
    item_type: Mapped[str] = mapped_column(sa.String(50), nullable=False)
    uom_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid(as_uuid=True),
        sa.ForeignKey("core.unit_of_measure.id", ondelete="RESTRICT"),
        nullable=False,
    )
    track_stock: Mapped[bool] = mapped_column(
        sa.Boolean,
        nullable=False,
        server_default=sa.text("true"),
    )
    is_active: Mapped[bool] = mapped_column(
        sa.Boolean,
        nullable=False,
        server_default=sa.text("true"),
    )
