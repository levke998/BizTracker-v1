"""Event ticket actual ORM model."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
import uuid

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class EventTicketActualModel(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Stores ticket-system actuals attached to one Flow event."""

    __tablename__ = "event_ticket_actual"
    __table_args__ = (
        sa.UniqueConstraint("event_id", name="uq_core_event_ticket_actual_event_id"),
        sa.Index("ix_core_event_ticket_actual_event_id", "event_id"),
        {"schema": "core"},
    )

    event_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid(as_uuid=True),
        sa.ForeignKey("core.event.id", ondelete="CASCADE"),
        nullable=False,
    )
    source_name: Mapped[str | None] = mapped_column(sa.String(120), nullable=True)
    source_reference: Mapped[str | None] = mapped_column(sa.String(180), nullable=True)
    sold_quantity: Mapped[Decimal] = mapped_column(
        sa.Numeric(12, 3),
        nullable=False,
        server_default=sa.text("0"),
    )
    gross_revenue: Mapped[Decimal] = mapped_column(
        sa.Numeric(14, 2),
        nullable=False,
        server_default=sa.text("0"),
    )
    net_revenue: Mapped[Decimal | None] = mapped_column(sa.Numeric(14, 2), nullable=True)
    vat_amount: Mapped[Decimal | None] = mapped_column(sa.Numeric(14, 2), nullable=True)
    vat_rate_id: Mapped[uuid.UUID | None] = mapped_column(
        sa.Uuid(as_uuid=True),
        sa.ForeignKey("core.vat_rate.id", ondelete="SET NULL"),
        nullable=True,
    )
    platform_fee_gross: Mapped[Decimal] = mapped_column(
        sa.Numeric(14, 2),
        nullable=False,
        server_default=sa.text("0"),
    )
    reported_at: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
