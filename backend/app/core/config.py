"""Application settings loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

ENV_FILE_PATH = Path(__file__).resolve().parents[2] / ".env"
BACKEND_ROOT = ENV_FILE_PATH.parent
DEFAULT_DEV_CORS_ORIGINS = (
    "http://localhost:5173",
    "http://127.0.0.1:5173",
)


def _strip_optional_quotes(value: str) -> str:
    """Remove matching single or double quotes around a value."""

    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def load_env_file(env_file_path: Path = ENV_FILE_PATH) -> None:
    """Load simple KEY=VALUE pairs from a local .env file into os.environ."""

    if not env_file_path.exists():
        return

    for raw_line in env_file_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), _strip_optional_quotes(value.strip()))


@dataclass(frozen=True)
class Settings:
    """Small immutable settings object for backend wiring."""

    app_env: str
    app_name: str
    api_v1_prefix: str
    secret_key: str
    database_url: str
    sqlalchemy_echo: bool
    cors_origins: tuple[str, ...]
    imports_storage_dir: Path


def _parse_bool(value: str | None, *, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _parse_csv(value: str | None) -> tuple[str, ...]:
    if not value:
        return ()
    return tuple(item.strip() for item in value.split(",") if item.strip())


def _resolve_path(value: str | None, *, default: Path) -> Path:
    if not value:
        return default

    path = Path(value)
    if not path.is_absolute():
        path = BACKEND_ROOT / path
    return path.resolve()


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""

    load_env_file()

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError(
            "DATABASE_URL is not set. Add it to backend/.env or the environment."
        )

    app_env = os.getenv("APP_ENV", "development")
    cors_origins = _parse_csv(os.getenv("CORS_ORIGINS"))
    if not cors_origins and app_env == "development":
        cors_origins = DEFAULT_DEV_CORS_ORIGINS

    return Settings(
        app_env=app_env,
        app_name=os.getenv("APP_NAME", "BizTracker"),
        api_v1_prefix=os.getenv("API_V1_PREFIX", "/api/v1"),
        secret_key=os.getenv("SECRET_KEY", "change-me"),
        database_url=database_url,
        sqlalchemy_echo=_parse_bool(os.getenv("SQLALCHEMY_ECHO"), default=False),
        cors_origins=cors_origins,
        imports_storage_dir=_resolve_path(
            os.getenv("IMPORTS_STORAGE_DIR"),
            default=BACKEND_ROOT / "storage" / "imports",
        ),
    )
