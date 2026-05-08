"""Purchase invoice PDF draft ORM model."""

from __future__ import annotations

import uuid

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class PurchaseInvoiceDraftModel(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Stores an uploaded supplier invoice PDF before user review and posting."""

    __tablename__ = "supplier_invoice_draft"
    __table_args__ = (
        sa.Index("ix_core_supplier_invoice_draft_business_unit_id", "business_unit_id"),
        sa.Index("ix_core_supplier_invoice_draft_supplier_id", "supplier_id"),
        sa.Index("ix_core_supplier_invoice_draft_status", "status"),
        {"schema": "core"},
    )

    business_unit_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid(as_uuid=True),
        sa.ForeignKey("core.business_unit.id", ondelete="RESTRICT"),
        nullable=False,
    )
    supplier_id: Mapped[uuid.UUID | None] = mapped_column(
        sa.Uuid(as_uuid=True),
        sa.ForeignKey("core.supplier.id", ondelete="SET NULL"),
        nullable=True,
    )
    original_name: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    stored_path: Mapped[str] = mapped_column(sa.String(500), nullable=False)
    mime_type: Mapped[str | None] = mapped_column(sa.String(255), nullable=True)
    size_bytes: Mapped[int] = mapped_column(sa.BigInteger, nullable=False)
    status: Mapped[str] = mapped_column(
        sa.String(50),
        nullable=False,
        server_default=sa.text("'review_required'"),
    )
    extraction_status: Mapped[str] = mapped_column(
        sa.String(50),
        nullable=False,
        server_default=sa.text("'not_started'"),
    )
    raw_extraction: Mapped[dict | None] = mapped_column(
        postgresql.JSONB(astext_type=sa.Text()),
        nullable=True,
    )
    review_payload: Mapped[dict | None] = mapped_column(
        postgresql.JSONB(astext_type=sa.Text()),
        nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
