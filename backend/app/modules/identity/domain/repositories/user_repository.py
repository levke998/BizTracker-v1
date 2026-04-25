"""Identity repository contract."""

from __future__ import annotations

import uuid
from typing import Protocol

from app.modules.identity.domain.entities.user import (
    AuthenticatedUser,
    UserCredentials,
)


class UserRepository(Protocol):
    """Defines persistence access for identity use cases."""

    def get_credentials_by_email(self, email: str) -> UserCredentials | None:
        """Return password verification data for one normalized email."""

    def get_authenticated_user_by_id(
        self,
        user_id: uuid.UUID,
    ) -> AuthenticatedUser | None:
        """Return an active user profile with role and permission codes."""

    def record_successful_login(self, user_id: uuid.UUID) -> None:
        """Update login metadata after successful authentication."""
