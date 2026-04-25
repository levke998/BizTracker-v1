"""Identity request and response schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class LoginRequest(BaseModel):
    """Login request for internal users."""

    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=1, max_length=256)


class CurrentUserResponse(BaseModel):
    """Current authenticated user response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    full_name: str
    is_active: bool
    roles: list[str]
    permissions: list[str]
    last_login_at: datetime | None
    created_at: datetime
    updated_at: datetime


class LoginResponse(BaseModel):
    """Successful login response with access token and user profile."""

    access_token: str
    token_type: str
    user: CurrentUserResponse
