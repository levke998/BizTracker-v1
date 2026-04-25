"""Estimated stock consumption audit ORM model."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
import uuid

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import UUIDPrimaryKeyMixin


class EstimatedConsumptionAuditModel(UUIDPrimaryKeyMixin, Base):
    """Explains one estimated stock decrease created by POS consumption rules."""

    __tablename__ = "estimated_consumption_audit"
    __table_args__ = (
        sa.UniqueConstraint(
            "source_type",
            "source_id",
            "product_id",
            "inventory_item_id",
            name="uq_core_estimated_consumption_source_product_item",
        ),
        sa.Index(
            "ix_core_estimated_consumption_business_unit_id",
            "business_unit_id",
        ),
        sa.Index(
            "ix_core_estimated_consumption_inventory_item_id",
            "inventory_item_id",
        ),
        sa.Index("ix_core_estimated_consumption_product_id", "product_id"),
        sa.Index("ix_core_estimated_consumption_source_ref", "source_type", "source_id"),
        {"schema": "core"},
    )

    business_unit_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid(as_uuid=True),
        sa.ForeignKey("core.business_unit.id", ondelete="RESTRICT"),
        nullable=False,
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid(as_uuid=True),
        sa.ForeignKey("core.product.id", ondelete="RESTRICT"),
        nullable=False,
    )
    inventory_item_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid(as_uuid=True),
        sa.ForeignKey("core.inventory_item.id", ondelete="RESTRICT"),
        nullable=False,
    )
    recipe_version_id: Mapped[uuid.UUID | None] = mapped_column(
        sa.Uuid(as_uuid=True),
        sa.ForeignKey("core.recipe_version.id", ondelete="SET NULL"),
        nullable=True,
    )
    source_type: Mapped[str] = mapped_column(sa.String(50), nullable=False)
    source_id: Mapped[uuid.UUID] = mapped_column(sa.Uuid(as_uuid=True), nullable=False)
    source_dedupe_key: Mapped[str | None] = mapped_column(sa.String(128), nullable=True)
    receipt_no: Mapped[str | None] = mapped_column(sa.String(100), nullable=True)
    estimation_basis: Mapped[str] = mapped_column(sa.String(50), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(sa.Numeric(14, 3), nullable=False)
    uom_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid(as_uuid=True),
        sa.ForeignKey("core.unit_of_measure.id", ondelete="RESTRICT"),
        nullable=False,
    )
    quantity_before: Mapped[Decimal] = mapped_column(sa.Numeric(14, 3), nullable=False)
    quantity_after: Mapped[Decimal] = mapped_column(sa.Numeric(14, 3), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
    )
