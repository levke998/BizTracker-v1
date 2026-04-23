"""Finance ORM model."""

from __future__ import annotations

from datetime import datetime
import uuid
from decimal import Decimal

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class FinancialTransactionModel(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Stores one mapped finance transaction."""

    __tablename__ = "financial_transaction"
    __table_args__ = (
        sa.UniqueConstraint(
            "source_type",
            "source_id",
            name="uq_core_financial_transaction_source_ref",
        ),
        sa.Index("ix_core_financial_transaction_business_unit_id", "business_unit_id"),
        sa.Index("ix_core_financial_transaction_occurred_at", "occurred_at"),
        sa.Index("ix_core_financial_transaction_transaction_type", "transaction_type"),
        {"schema": "core"},
    )

    business_unit_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid(as_uuid=True),
        sa.ForeignKey("core.business_unit.id", ondelete="RESTRICT"),
        nullable=False,
    )
    direction: Mapped[str] = mapped_column(sa.String(20), nullable=False)
    transaction_type: Mapped[str] = mapped_column(sa.String(100), nullable=False)
    amount: Mapped[Decimal] = mapped_column(sa.Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(sa.String(3), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
    )
    description: Mapped[str] = mapped_column(sa.Text, nullable=False)
    source_type: Mapped[str] = mapped_column(sa.String(100), nullable=False)
    source_id: Mapped[uuid.UUID] = mapped_column(sa.Uuid(as_uuid=True), nullable=False)
