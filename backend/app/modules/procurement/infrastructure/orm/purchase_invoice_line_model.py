"""Purchase invoice line ORM model."""

from __future__ import annotations

import uuid
from decimal import Decimal

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import UUIDPrimaryKeyMixin


class PurchaseInvoiceLineModel(UUIDPrimaryKeyMixin, Base):
    """Line storage model for procurement purchase invoices."""

    __tablename__ = "supplier_invoice_line"
    __table_args__ = (
        sa.Index("ix_core_supplier_invoice_line_invoice_id", "invoice_id"),
        sa.Index("ix_core_supplier_invoice_line_inventory_item_id", "inventory_item_id"),
        {"schema": "core"},
    )

    invoice_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid(as_uuid=True),
        sa.ForeignKey("core.supplier_invoice.id", ondelete="CASCADE"),
        nullable=False,
    )
    inventory_item_id: Mapped[uuid.UUID | None] = mapped_column(
        sa.Uuid(as_uuid=True),
        sa.ForeignKey("core.inventory_item.id", ondelete="RESTRICT"),
        nullable=True,
    )
    description: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(sa.Numeric(14, 3), nullable=False)
    uom_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid(as_uuid=True),
        sa.ForeignKey("core.unit_of_measure.id", ondelete="RESTRICT"),
        nullable=False,
    )
    unit_net_amount: Mapped[Decimal] = mapped_column(sa.Numeric(14, 2), nullable=False)
    line_net_amount: Mapped[Decimal] = mapped_column(sa.Numeric(14, 2), nullable=False)
    vat_rate_id: Mapped[uuid.UUID | None] = mapped_column(
        sa.Uuid(as_uuid=True),
        sa.ForeignKey("core.vat_rate.id", ondelete="SET NULL"),
        nullable=True,
    )
    vat_amount: Mapped[Decimal | None] = mapped_column(sa.Numeric(14, 2), nullable=True)
    line_gross_amount: Mapped[Decimal | None] = mapped_column(
        sa.Numeric(14, 2),
        nullable=True,
    )

    invoice: Mapped["PurchaseInvoiceModel"] = relationship(
        "PurchaseInvoiceModel",
        back_populates="lines",
    )
