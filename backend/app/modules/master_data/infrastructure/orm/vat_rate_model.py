"""VAT rate ORM model."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class VatRateModel(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Stores official and configurable VAT rates used for calculations."""

    __tablename__ = "vat_rate"
    __table_args__ = (
        sa.UniqueConstraint("code", name="uq_core_vat_rate_code"),
        sa.Index("ix_core_vat_rate_is_active", "is_active"),
        {"schema": "core"},
    )

    code: Mapped[str] = mapped_column(sa.String(40), nullable=False)
    name: Mapped[str] = mapped_column(sa.String(120), nullable=False)
    rate_percent: Mapped[Decimal] = mapped_column(sa.Numeric(7, 4), nullable=False)
    rate_type: Mapped[str] = mapped_column(
        sa.String(40),
        nullable=False,
        server_default=sa.text("'standard'"),
    )
    nav_code: Mapped[str | None] = mapped_column(sa.String(80), nullable=True)
    description: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    valid_from: Mapped[date | None] = mapped_column(sa.Date, nullable=True)
    valid_to: Mapped[date | None] = mapped_column(sa.Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(
        sa.Boolean,
        nullable=False,
        server_default=sa.text("true"),
    )
