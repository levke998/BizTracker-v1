"""Inventory variance threshold ORM model."""

from __future__ import annotations

import uuid
from decimal import Decimal

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class InventoryVarianceThresholdModel(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Business-unit specific thresholds for inventory controlling decisions."""

    __tablename__ = "inventory_variance_threshold"
    __table_args__ = (
        sa.UniqueConstraint(
            "business_unit_id",
            name="uq_core_inventory_variance_threshold_business_unit_id",
        ),
        sa.Index(
            "ix_core_inventory_variance_threshold_business_unit_id",
            "business_unit_id",
        ),
        {"schema": "core"},
    )

    business_unit_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid(as_uuid=True),
        sa.ForeignKey("core.business_unit.id", ondelete="CASCADE"),
        nullable=False,
    )
    high_loss_value_threshold: Mapped[Decimal] = mapped_column(
        sa.Numeric(14, 2),
        nullable=False,
        server_default=sa.text("10000.00"),
    )
    worsening_percent_threshold: Mapped[Decimal] = mapped_column(
        sa.Numeric(7, 2),
        nullable=False,
        server_default=sa.text("25.00"),
    )
