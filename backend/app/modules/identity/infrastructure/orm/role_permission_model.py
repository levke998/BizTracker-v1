"""Association ORM model between roles and permissions."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
import uuid

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.modules.identity.infrastructure.orm.permission_model import PermissionModel
    from app.modules.identity.infrastructure.orm.role_model import RoleModel


class RolePermissionModel(Base):
    """Links roles to permissions."""

    __tablename__ = "role_permission"
    __table_args__ = (
        sa.Index("ix_auth_role_permission_permission_id", "permission_id"),
        {"schema": "auth"},
    )

    role_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid(as_uuid=True),
        sa.ForeignKey("auth.role.id", ondelete="CASCADE"),
        primary_key=True,
    )
    permission_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid(as_uuid=True),
        sa.ForeignKey("auth.permission.id", ondelete="CASCADE"),
        primary_key=True,
    )
    assigned_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
    )

    role: Mapped["RoleModel"] = relationship(back_populates="role_permissions")
    permission: Mapped["PermissionModel"] = relationship(
        back_populates="role_permissions"
    )
