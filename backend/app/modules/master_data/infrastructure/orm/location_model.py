"""Location ORM model."""

from __future__ import annotations

from typing import TYPE_CHECKING
import uuid

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.modules.master_data.infrastructure.orm.business_unit_model import (
        BusinessUnitModel,
    )


class LocationModel(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Physical site belonging to a business unit."""

    __tablename__ = "location"
    __table_args__ = (
        sa.UniqueConstraint(
            "business_unit_id",
            "name",
            name="uq_core_location_business_unit_name",
        ),
        sa.Index("ix_core_location_business_unit_id", "business_unit_id"),
        {"schema": "core"},
    )

    business_unit_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid(as_uuid=True),
        sa.ForeignKey("core.business_unit.id", ondelete="RESTRICT"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(sa.String(150), nullable=False)
    kind: Mapped[str] = mapped_column(sa.String(50), nullable=False)
    is_active: Mapped[bool] = mapped_column(
        sa.Boolean,
        nullable=False,
        server_default=sa.text("true"),
    )

    business_unit: Mapped["BusinessUnitModel"] = relationship(
        back_populates="locations"
    )
