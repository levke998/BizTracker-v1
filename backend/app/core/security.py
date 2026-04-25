"""Security helpers for password hashing and signed access tokens."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from app.core.config import get_settings

PASSWORD_HASH_ALGORITHM = "pbkdf2_sha256"
PASSWORD_HASH_ITERATIONS = 210_000
TOKEN_ALGORITHM = "HS256"
ACCESS_TOKEN_TYPE = "access"


class InvalidTokenError(Exception):
    """Raised when a token cannot be trusted."""


def normalize_email(email: str) -> str:
    """Normalize an email for identity lookup."""

    return email.strip().lower()


def hash_password(password: str) -> str:
    """Hash a password with PBKDF2-HMAC-SHA256 and a per-password salt."""

    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PASSWORD_HASH_ITERATIONS,
    )
    return (
        f"{PASSWORD_HASH_ALGORITHM}${PASSWORD_HASH_ITERATIONS}$"
        f"{_base64url_encode(salt)}${_base64url_encode(digest)}"
    )


def verify_password(password: str, password_hash: str) -> bool:
    """Return whether the plain password matches the stored password hash."""

    try:
        algorithm, iterations_text, salt_text, digest_text = password_hash.split("$", 3)
        if algorithm != PASSWORD_HASH_ALGORITHM:
            return False

        iterations = int(iterations_text)
        salt = _base64url_decode(salt_text)
        expected_digest = _base64url_decode(digest_text)
    except (TypeError, ValueError):
        return False

    actual_digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        iterations,
    )
    return hmac.compare_digest(actual_digest, expected_digest)


def create_access_token(*, subject: uuid.UUID, expires_delta: timedelta | None = None) -> str:
    """Create a compact HMAC-signed access token."""

    settings = get_settings()
    now = datetime.now(UTC)
    expires_at = now + (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=settings.access_token_expire_minutes)
    )
    payload = {
        "sub": str(subject),
        "typ": ACCESS_TOKEN_TYPE,
        "iat": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
    }
    return _encode_token(payload, settings.secret_key)


def decode_access_token(token: str) -> uuid.UUID:
    """Validate a signed access token and return its subject user id."""

    settings = get_settings()
    payload = _decode_token(token, settings.secret_key)

    if payload.get("typ") != ACCESS_TOKEN_TYPE:
        raise InvalidTokenError("Invalid token type.")

    expires_at = payload.get("exp")
    if not isinstance(expires_at, int):
        raise InvalidTokenError("Token expiration is missing.")
    if datetime.now(UTC).timestamp() >= expires_at:
        raise InvalidTokenError("Token has expired.")

    subject = payload.get("sub")
    if not isinstance(subject, str):
        raise InvalidTokenError("Token subject is missing.")

    try:
        return uuid.UUID(subject)
    except ValueError as exc:
        raise InvalidTokenError("Token subject is invalid.") from exc


def _encode_token(payload: dict[str, Any], secret_key: str) -> str:
    header = {"alg": TOKEN_ALGORITHM, "typ": "JWT"}
    header_text = _base64url_encode(
        json.dumps(header, separators=(",", ":"), sort_keys=True).encode("utf-8")
    )
    payload_text = _base64url_encode(
        json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    )
    signing_input = f"{header_text}.{payload_text}"
    signature = _sign(signing_input, secret_key)
    return f"{signing_input}.{signature}"


def _decode_token(token: str, secret_key: str) -> dict[str, Any]:
    try:
        header_text, payload_text, signature = token.split(".", 2)
    except ValueError as exc:
        raise InvalidTokenError("Malformed token.") from exc

    signing_input = f"{header_text}.{payload_text}"
    expected_signature = _sign(signing_input, secret_key)
    if not hmac.compare_digest(signature, expected_signature):
        raise InvalidTokenError("Invalid token signature.")

    try:
        header = json.loads(_base64url_decode(header_text))
        if header.get("alg") != TOKEN_ALGORITHM:
            raise InvalidTokenError("Unsupported token algorithm.")
        payload = json.loads(_base64url_decode(payload_text))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise InvalidTokenError("Invalid token payload.") from exc

    if not isinstance(payload, dict):
        raise InvalidTokenError("Invalid token payload.")
    return payload


def _sign(value: str, secret_key: str) -> str:
    digest = hmac.new(
        secret_key.encode("utf-8"),
        value.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    return _base64url_encode(digest)


def _base64url_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _base64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(f"{value}{padding}".encode("ascii"))
