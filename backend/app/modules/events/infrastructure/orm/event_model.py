"""Event ORM model."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
import uuid

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class EventModel(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Stores Flow-style event planning and settlement-lite inputs."""

    __tablename__ = "event"
    __table_args__ = (
        sa.Index("ix_core_event_business_unit_id", "business_unit_id"),
        sa.Index("ix_core_event_location_id", "location_id"),
        sa.Index("ix_core_event_starts_at", "starts_at"),
        sa.Index("ix_core_event_status", "status"),
        {"schema": "core"},
    )

    business_unit_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid(as_uuid=True),
        sa.ForeignKey("core.business_unit.id", ondelete="RESTRICT"),
        nullable=False,
    )
    location_id: Mapped[uuid.UUID | None] = mapped_column(
        sa.Uuid(as_uuid=True),
        sa.ForeignKey("core.location.id", ondelete="SET NULL"),
        nullable=True,
    )
    title: Mapped[str] = mapped_column(sa.String(180), nullable=False)
    status: Mapped[str] = mapped_column(
        sa.String(30),
        nullable=False,
        server_default=sa.text("'planned'"),
    )
    starts_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False)
    ends_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True), nullable=True)
    performer_name: Mapped[str | None] = mapped_column(sa.String(180), nullable=True)
    expected_attendance: Mapped[int | None] = mapped_column(sa.Integer, nullable=True)
    ticket_revenue_gross: Mapped[Decimal] = mapped_column(
        sa.Numeric(14, 2),
        nullable=False,
        server_default=sa.text("0"),
    )
    bar_revenue_gross: Mapped[Decimal] = mapped_column(
        sa.Numeric(14, 2),
        nullable=False,
        server_default=sa.text("0"),
    )
    performer_share_percent: Mapped[Decimal] = mapped_column(
        sa.Numeric(5, 2),
        nullable=False,
        server_default=sa.text("80"),
    )
    performer_fixed_fee: Mapped[Decimal] = mapped_column(
        sa.Numeric(14, 2),
        nullable=False,
        server_default=sa.text("0"),
    )
    event_cost_amount: Mapped[Decimal] = mapped_column(
        sa.Numeric(14, 2),
        nullable=False,
        server_default=sa.text("0"),
    )
    notes: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(
        sa.Boolean,
        nullable=False,
        server_default=sa.text("true"),
    )
