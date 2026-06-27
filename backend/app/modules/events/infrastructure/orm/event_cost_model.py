"""Event cost line ORM model."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
import uuid

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class EventCostLineModel(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Stores auditable gross cost lines attached to one Flow event."""

    __tablename__ = "event_cost_line"
    __table_args__ = (
        sa.Index("ix_core_event_cost_line_event_id", "event_id"),
        sa.Index("ix_core_event_cost_line_category", "category"),
        {"schema": "core"},
    )

    event_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid(as_uuid=True),
        sa.ForeignKey("core.event.id", ondelete="CASCADE"),
        nullable=False,
    )
    category: Mapped[str] = mapped_column(sa.String(80), nullable=False)
    description: Mapped[str] = mapped_column(sa.String(240), nullable=False)
    amount_gross: Mapped[Decimal] = mapped_column(
        sa.Numeric(14, 2),
        nullable=False,
        server_default=sa.text("0"),
    )
    source_type: Mapped[str] = mapped_column(
        sa.String(40),
        nullable=False,
        server_default=sa.text("'manual'"),
    )
    source_reference: Mapped[str | None] = mapped_column(sa.String(180), nullable=True)
    incurred_at: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
