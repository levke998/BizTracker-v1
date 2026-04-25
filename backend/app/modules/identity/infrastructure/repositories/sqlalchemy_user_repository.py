"""Identity SQLAlchemy repository."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.modules.identity.domain.entities.user import (
    AuthenticatedUser,
    UserCredentials,
)
from app.modules.identity.infrastructure.orm.role_model import RoleModel
from app.modules.identity.infrastructure.orm.role_permission_model import (
    RolePermissionModel,
)
from app.modules.identity.infrastructure.orm.user_model import UserModel
from app.modules.identity.infrastructure.orm.user_role_model import UserRoleModel


class SqlAlchemyUserRepository:
    """SQLAlchemy-backed repository for internal users."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_credentials_by_email(self, email: str) -> UserCredentials | None:
        model = self._session.scalar(select(UserModel).where(UserModel.email == email))
        if model is None:
            return None

        return UserCredentials(
            id=model.id,
            email=model.email,
            password_hash=model.password_hash,
            is_active=model.is_active,
        )

    def get_authenticated_user_by_id(
        self,
        user_id: uuid.UUID,
    ) -> AuthenticatedUser | None:
        model = self._session.scalar(
            select(UserModel)
            .options(
                selectinload(UserModel.user_roles)
                .selectinload(UserRoleModel.role)
                .selectinload(RoleModel.role_permissions)
                .selectinload(RolePermissionModel.permission)
            )
            .where(UserModel.id == user_id)
        )
        if model is None or not model.is_active:
            return None

        return self._to_authenticated_user(model)

    def record_successful_login(self, user_id: uuid.UUID) -> None:
        model = self._session.get(UserModel, user_id)
        if model is None:
            return

        model.last_login_at = datetime.now(UTC)
        self._session.commit()

    @staticmethod
    def _to_authenticated_user(model: UserModel) -> AuthenticatedUser:
        roles = sorted(
            user_role.role.code
            for user_role in model.user_roles
            if user_role.role.is_active
        )
        permissions = sorted(
            {
                role_permission.permission.code
                for user_role in model.user_roles
                if user_role.role.is_active
                for role_permission in user_role.role.role_permissions
            }
        )
        return AuthenticatedUser(
            id=model.id,
            email=model.email,
            full_name=model.full_name,
            is_active=model.is_active,
            roles=roles,
            permissions=permissions,
            last_login_at=model.last_login_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
