"""Purchase invoice ORM model."""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class PurchaseInvoiceModel(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Header storage model for procurement purchase invoices."""

    __tablename__ = "supplier_invoice"
    __table_args__ = (
        sa.UniqueConstraint(
            "business_unit_id",
            "supplier_id",
            "invoice_number",
            name="uq_core_supplier_invoice_business_unit_supplier_invoice_number",
        ),
        sa.Index("ix_core_supplier_invoice_business_unit_id", "business_unit_id"),
        sa.Index("ix_core_supplier_invoice_supplier_id", "supplier_id"),
        sa.Index("ix_core_supplier_invoice_invoice_date", "invoice_date"),
        {"schema": "core"},
    )

    business_unit_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid(as_uuid=True),
        sa.ForeignKey("core.business_unit.id", ondelete="RESTRICT"),
        nullable=False,
    )
    supplier_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid(as_uuid=True),
        sa.ForeignKey("core.supplier.id", ondelete="RESTRICT"),
        nullable=False,
    )
    invoice_number: Mapped[str] = mapped_column(sa.String(120), nullable=False)
    invoice_date: Mapped[date] = mapped_column(sa.Date, nullable=False)
    currency: Mapped[str] = mapped_column(
        sa.String(3),
        nullable=False,
        server_default=sa.text("'HUF'"),
    )
    gross_total: Mapped[Decimal] = mapped_column(sa.Numeric(14, 2), nullable=False)
    notes: Mapped[str | None] = mapped_column(sa.Text, nullable=True)

    lines: Mapped[list["PurchaseInvoiceLineModel"]] = relationship(
        "PurchaseInvoiceLineModel",
        back_populates="invoice",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
