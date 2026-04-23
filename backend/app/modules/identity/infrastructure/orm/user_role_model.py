"""Association ORM model between users and roles."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
import uuid

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.modules.identity.infrastructure.orm.role_model import RoleModel
    from app.modules.identity.infrastructure.orm.user_model import UserModel


class UserRoleModel(Base):
    """Links users to roles."""

    __tablename__ = "user_role"
    __table_args__ = (
        sa.Index("ix_auth_user_role_role_id", "role_id"),
        {"schema": "auth"},
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid(as_uuid=True),
        sa.ForeignKey("auth.user.id", ondelete="CASCADE"),
        primary_key=True,
    )
    role_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid(as_uuid=True),
        sa.ForeignKey("auth.role.id", ondelete="CASCADE"),
        primary_key=True,
    )
    assigned_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
    )

    user: Mapped["UserModel"] = relationship(back_populates="user_roles")
    role: Mapped["RoleModel"] = relationship(back_populates="user_roles")
