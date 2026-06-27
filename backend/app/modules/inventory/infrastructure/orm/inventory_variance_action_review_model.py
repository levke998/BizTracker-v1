"""Inventory variance action review ORM model."""

from __future__ import annotations

import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class InventoryVarianceActionReviewModel(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Persisted review state for generated inventory action suggestions."""

    __tablename__ = "inventory_variance_action_review"
    __table_args__ = (
        sa.UniqueConstraint(
            "business_unit_id",
            "suggestion_id",
            name="uq_core_inventory_variance_action_review_unit_suggestion",
        ),
        sa.Index(
            "ix_core_inventory_variance_action_review_business_unit_id",
            "business_unit_id",
        ),
        sa.Index(
            "ix_core_inventory_variance_action_review_suggestion_id",
            "suggestion_id",
        ),
        {"schema": "core"},
    )

    business_unit_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid(as_uuid=True),
        sa.ForeignKey("core.business_unit.id", ondelete="CASCADE"),
        nullable=False,
    )
    suggestion_id: Mapped[str] = mapped_column(sa.String(220), nullable=False)
    status: Mapped[str] = mapped_column(
        sa.String(30),
        nullable=False,
        server_default=sa.text("'open'"),
    )
    note: Mapped[str | None] = mapped_column(sa.String(500), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=True,
    )
