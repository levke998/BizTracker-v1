"""Identity permission ORM model."""

from __future__ import annotations

from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.modules.identity.infrastructure.orm.role_permission_model import (
        RolePermissionModel,
    )


class PermissionModel(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Stores fine-grained permissions."""

    __tablename__ = "permission"
    __table_args__ = (
        sa.UniqueConstraint("code", name="uq_auth_permission_code"),
        sa.Index("ix_auth_permission_code", "code"),
        {"schema": "auth"},
    )

    code: Mapped[str] = mapped_column(sa.String(100), nullable=False)
    name: Mapped[str] = mapped_column(sa.String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(sa.String(255), nullable=True)

    role_permissions: Mapped[list["RolePermissionModel"]] = relationship(
        back_populates="permission",
        cascade="all, delete-orphan",
    )
