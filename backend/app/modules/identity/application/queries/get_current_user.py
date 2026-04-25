"""Get current user query."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from app.modules.identity.domain.entities.user import AuthenticatedUser
from app.modules.identity.domain.repositories.user_repository import UserRepository


class CurrentUserNotFoundError(Exception):
    """Raised when token subject does not point to an active user."""


@dataclass(slots=True)
class GetCurrentUserQuery:
    """Return the current authenticated user."""

    repository: UserRepository

    def execute(self, *, user_id: uuid.UUID) -> AuthenticatedUser:
        user = self.repository.get_authenticated_user_by_id(user_id)
        if user is None:
            raise CurrentUserNotFoundError("Current user was not found.")
        return user
