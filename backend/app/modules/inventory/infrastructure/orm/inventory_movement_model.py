"""Inventory movement ORM model."""

from __future__ import annotations

import uuid
from decimal import Decimal
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import UUIDPrimaryKeyMixin


class InventoryMovementModel(UUIDPrimaryKeyMixin, Base):
    """Append-only inventory movement log used by later stock calculations."""

    __tablename__ = "inventory_movement"
    __table_args__ = (
        sa.UniqueConstraint(
            "source_type",
            "source_id",
            name="uq_core_inventory_movement_source_ref",
        ),
        sa.Index("ix_core_inventory_movement_business_unit_id", "business_unit_id"),
        sa.Index("ix_core_inventory_movement_inventory_item_id", "inventory_item_id"),
        sa.Index("ix_core_inventory_movement_occurred_at", "occurred_at"),
        sa.Index("ix_core_inventory_movement_source_ref", "source_type", "source_id"),
        {"schema": "core"},
    )

    business_unit_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid(as_uuid=True),
        sa.ForeignKey("core.business_unit.id", ondelete="RESTRICT"),
        nullable=False,
    )
    inventory_item_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid(as_uuid=True),
        sa.ForeignKey("core.inventory_item.id", ondelete="RESTRICT"),
        nullable=False,
    )
    movement_type: Mapped[str] = mapped_column(sa.String(50), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(sa.Numeric(12, 3), nullable=False)
    uom_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid(as_uuid=True),
        sa.ForeignKey("core.unit_of_measure.id", ondelete="RESTRICT"),
        nullable=False,
    )
    unit_cost: Mapped[Decimal | None] = mapped_column(sa.Numeric(12, 2), nullable=True)
    note: Mapped[str | None] = mapped_column(sa.String(500), nullable=True)
    source_type: Mapped[str | None] = mapped_column(sa.String(100), nullable=True)
    source_id: Mapped[uuid.UUID | None] = mapped_column(sa.Uuid(as_uuid=True), nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.text("now()"),
    )
