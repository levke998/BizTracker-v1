"""Login use case."""

from __future__ import annotations

from dataclasses import dataclass

from app.core.security import create_access_token, normalize_email, verify_password
from app.modules.identity.domain.entities.user import AuthenticatedUser
from app.modules.identity.domain.repositories.user_repository import UserRepository


class InvalidLoginError(Exception):
    """Raised when authentication fails without leaking which field was wrong."""


@dataclass(frozen=True, slots=True)
class LoginResult:
    """Successful login result returned to the presentation layer."""

    access_token: str
    token_type: str
    user: AuthenticatedUser


@dataclass(slots=True)
class LoginCommand:
    """Authenticate a user and issue a signed access token."""

    repository: UserRepository

    def execute(self, *, email: str, password: str) -> LoginResult:
        normalized_email = normalize_email(email)
        credentials = self.repository.get_credentials_by_email(normalized_email)

        if credentials is None or not credentials.is_active:
            raise InvalidLoginError("Invalid email or password.")
        if not verify_password(password, credentials.password_hash):
            raise InvalidLoginError("Invalid email or password.")

        self.repository.record_successful_login(credentials.id)
        user = self.repository.get_authenticated_user_by_id(credentials.id)
        if user is None:
            raise InvalidLoginError("Invalid email or password.")

        return LoginResult(
            access_token=create_access_token(subject=user.id),
            token_type="bearer",
            user=user,
        )
