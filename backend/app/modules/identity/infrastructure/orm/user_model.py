"""Identity user ORM model."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.modules.identity.infrastructure.orm.user_role_model import UserRoleModel


class UserModel(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Stores internal users for authentication."""

    __tablename__ = "user"
    __table_args__ = (
        sa.UniqueConstraint("email", name="uq_auth_user_email"),
        sa.Index("ix_auth_user_email", "email"),
        {"schema": "auth"},
    )

    email: Mapped[str] = mapped_column(sa.String(320), nullable=False)
    password_hash: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(sa.String(200), nullable=False)
    is_active: Mapped[bool] = mapped_column(
        sa.Boolean,
        nullable=False,
        server_default=sa.text("true"),
    )
    last_login_at: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=True,
    )

    user_roles: Mapped[list["UserRoleModel"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
