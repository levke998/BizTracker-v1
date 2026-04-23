"""Supplier ORM model."""

from __future__ import annotations

import uuid

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class SupplierModel(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Read/write storage model for procurement suppliers."""

    __tablename__ = "supplier"
    __table_args__ = (
        sa.UniqueConstraint(
            "business_unit_id",
            "name",
            name="uq_core_supplier_business_unit_name",
        ),
        sa.Index("ix_core_supplier_business_unit_id", "business_unit_id"),
        sa.Index("ix_core_supplier_name", "name"),
        {"schema": "core"},
    )

    business_unit_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid(as_uuid=True),
        sa.ForeignKey("core.business_unit.id", ondelete="RESTRICT"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(sa.String(180), nullable=False)
    tax_id: Mapped[str | None] = mapped_column(sa.String(80), nullable=True)
    contact_name: Mapped[str | None] = mapped_column(sa.String(150), nullable=True)
    email: Mapped[str | None] = mapped_column(sa.String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(sa.String(80), nullable=True)
    notes: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(
        sa.Boolean,
        nullable=False,
        server_default=sa.text("true"),
    )
