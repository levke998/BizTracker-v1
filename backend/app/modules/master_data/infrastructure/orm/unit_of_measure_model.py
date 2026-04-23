"""Unit of measure ORM model."""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class UnitOfMeasureModel(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Shared unit of measure reference data."""

    __tablename__ = "unit_of_measure"
    __table_args__ = (
        sa.UniqueConstraint("code", name="uq_core_unit_of_measure_code"),
        sa.Index("ix_core_unit_of_measure_code", "code"),
        {"schema": "core"},
    )

    code: Mapped[str] = mapped_column(sa.String(20), nullable=False)
    name: Mapped[str] = mapped_column(sa.String(100), nullable=False)
    symbol: Mapped[str | None] = mapped_column(sa.String(20), nullable=True)
