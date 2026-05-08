"""Supplier invoice item alias ORM model."""

from __future__ import annotations

import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class SupplierItemAliasModel(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Stores supplier item names mapped to internal inventory items."""

    __tablename__ = "supplier_item_alias"
    __table_args__ = (
        sa.UniqueConstraint(
            "business_unit_id",
            "supplier_id",
            "source_item_key",
            name="uq_core_supplier_item_alias_source",
        ),
        sa.Index("ix_core_supplier_item_alias_business_unit_id", "business_unit_id"),
        sa.Index("ix_core_supplier_item_alias_supplier_id", "supplier_id"),
        sa.Index("ix_core_supplier_item_alias_inventory_item_id", "inventory_item_id"),
        sa.Index("ix_core_supplier_item_alias_status", "status"),
        {"schema": "core"},
    )

    business_unit_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid(as_uuid=True),
        sa.ForeignKey("core.business_unit.id", ondelete="RESTRICT"),
        nullable=False,
    )
    supplier_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid(as_uuid=True),
        sa.ForeignKey("core.supplier.id", ondelete="CASCADE"),
        nullable=False,
    )
    inventory_item_id: Mapped[uuid.UUID | None] = mapped_column(
        sa.Uuid(as_uuid=True),
        sa.ForeignKey("core.inventory_item.id", ondelete="SET NULL"),
        nullable=True,
    )
    source_item_name: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    source_item_key: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    internal_display_name: Mapped[str | None] = mapped_column(sa.String(255), nullable=True)
    status: Mapped[str] = mapped_column(
        sa.String(50),
        nullable=False,
        server_default=sa.text("'review_required'"),
    )
    mapping_confidence: Mapped[str] = mapped_column(
        sa.String(50),
        nullable=False,
        server_default=sa.text("'manual_review'"),
    )
    occurrence_count: Mapped[int] = mapped_column(
        sa.Integer,
        nullable=False,
        server_default=sa.text("0"),
    )
    first_seen_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
    )
    notes: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
