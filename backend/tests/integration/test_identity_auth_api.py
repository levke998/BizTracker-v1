"""Integration tests for identity/auth APIs."""

from __future__ import annotations

from collections.abc import Generator
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.core.security import hash_password, normalize_email
from app.modules.identity.infrastructure.orm.user_model import UserModel


@pytest.fixture
def auth_user(db_session: Session) -> Generator[tuple[str, str, UserModel], None, None]:
    """Create one active internal user for auth API tests."""

    email = normalize_email(f"auth-{uuid4().hex[:8]}@example.com")
    password = "CorrectHorseBatteryStaple123!"
    user = UserModel(
        email=email,
        password_hash=hash_password(password),
        full_name="Auth Test User",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    yield email, password, user

    db_session.rollback()
    db_session.execute(delete(UserModel).where(UserModel.id == user.id))
    db_session.commit()


def test_login_succeeds_with_valid_credentials(
    client: TestClient,
    auth_user: tuple[str, str, UserModel],
) -> None:
    email, password, user = auth_user

    response = client.post(
        "/api/v1/auth/login",
        json={"email": email.upper(), "password": password},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["token_type"] == "bearer"
    assert payload["access_token"]
    assert payload["user"]["id"] == str(user.id)
    assert payload["user"]["email"] == email
    assert payload["user"]["is_active"] is True


def test_login_rejects_invalid_credentials(
    client: TestClient,
    auth_user: tuple[str, str, UserModel],
) -> None:
    email, _, _ = auth_user

    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "wrong-password"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password."


def test_get_me_returns_current_user_with_valid_token(
    client: TestClient,
    auth_user: tuple[str, str, UserModel],
) -> None:
    email, password, user = auth_user
    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    token = login_response.json()["access_token"]

    response = client.get(
        "/api/v1/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == str(user.id)
    assert payload["email"] == email
    assert payload["full_name"] == "Auth Test User"


def test_get_me_without_token_returns_unauthorized(client: TestClient) -> None:
    response = client.get("/api/v1/me")

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated."
