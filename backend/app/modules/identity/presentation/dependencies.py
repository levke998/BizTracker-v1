"""Identity presentation dependency wiring."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import InvalidTokenError, decode_access_token
from app.db.session import get_db_session
from app.modules.identity.application.commands.login import LoginCommand
from app.modules.identity.application.queries.get_current_user import (
    CurrentUserNotFoundError,
    GetCurrentUserQuery,
)
from app.modules.identity.domain.entities.user import AuthenticatedUser
from app.modules.identity.infrastructure.repositories.sqlalchemy_user_repository import (
    SqlAlchemyUserRepository,
)

DbSession = Annotated[Session, Depends(get_db_session)]

bearer_scheme = HTTPBearer(auto_error=False)


def get_login_command(session: DbSession) -> LoginCommand:
    """Wire the login command to its repository."""

    repository = SqlAlchemyUserRepository(session)
    return LoginCommand(repository=repository)


def get_current_user_query(session: DbSession) -> GetCurrentUserQuery:
    """Wire the current user query to its repository."""

    repository = SqlAlchemyUserRepository(session)
    return GetCurrentUserQuery(repository=repository)


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    query: Annotated[GetCurrentUserQuery, Depends(get_current_user_query)],
) -> AuthenticatedUser:
    """Require a valid bearer access token and return the active user."""

    if credentials is None:
        raise _unauthorized()

    try:
        user_id = decode_access_token(credentials.credentials)
        return query.execute(user_id=user_id)
    except (InvalidTokenError, CurrentUserNotFoundError) as exc:
        raise _unauthorized() from exc


def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated.",
        headers={"WWW-Authenticate": "Bearer"},
    )
