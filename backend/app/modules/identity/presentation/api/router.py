"""Identity API routes."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.modules.identity.application.commands.login import (
    InvalidLoginError,
    LoginCommand,
)
from app.modules.identity.domain.entities.user import AuthenticatedUser
from app.modules.identity.presentation.dependencies import (
    get_current_user,
    get_login_command,
)
from app.modules.identity.presentation.schemas.auth import (
    CurrentUserResponse,
    LoginRequest,
    LoginResponse,
)

router = APIRouter(tags=["identity"])


@router.post("/auth/login", response_model=LoginResponse)
def login(
    payload: LoginRequest,
    command: Annotated[LoginCommand, Depends(get_login_command)],
) -> LoginResponse:
    """Authenticate an internal user and return an access token."""

    try:
        result = command.execute(email=payload.email, password=payload.password)
    except InvalidLoginError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        ) from exc

    return LoginResponse(
        access_token=result.access_token,
        token_type=result.token_type,
        user=CurrentUserResponse.model_validate(result.user),
    )


@router.get("/me", response_model=CurrentUserResponse)
def get_me(
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
) -> CurrentUserResponse:
    """Return the current user for a valid bearer token."""

    return CurrentUserResponse.model_validate(current_user)
