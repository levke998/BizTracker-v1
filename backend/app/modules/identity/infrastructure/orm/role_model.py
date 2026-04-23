"""Identity role ORM model."""

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
    from app.modules.identity.infrastructure.orm.user_role_model import UserRoleModel


class RoleModel(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Stores authorization roles."""

    __tablename__ = "role"
    __table_args__ = (
        sa.UniqueConstraint("code", name="uq_auth_role_code"),
        sa.Index("ix_auth_role_code", "code"),
        {"schema": "auth"},
    )

    code: Mapped[str] = mapped_column(sa.String(50), nullable=False)
    name: Mapped[str] = mapped_column(sa.String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(sa.String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(
        sa.Boolean,
        nullable=False,
        server_default=sa.text("true"),
    )

    user_roles: Mapped[list["UserRoleModel"]] = relationship(
        back_populates="role",
        cascade="all, delete-orphan",
    )
    role_permissions: Mapped[list["RolePermissionModel"]] = relationship(
        back_populates="role",
        cascade="all, delete-orphan",
    )
