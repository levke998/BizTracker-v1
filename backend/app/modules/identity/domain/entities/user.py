"""Identity domain entities."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class AuthenticatedUser:
    """Internal user with the role and permission codes needed by the UI."""

    id: uuid.UUID
    email: str
    full_name: str
    is_active: bool
    roles: list[str]
    permissions: list[str]
    last_login_at: datetime | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class UserCredentials:
    """Credentials data required by the login use case."""

    id: uuid.UUID
    email: str
    password_hash: str
    is_active: bool
