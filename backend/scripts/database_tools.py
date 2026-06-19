"""Shared helpers for local PostgreSQL backup and restore scripts."""

from __future__ import annotations

import os
import shutil
from pathlib import Path

from sqlalchemy.engine import URL, make_url

from app.core.config import get_settings

LOCAL_DATABASE_HOSTS = {"localhost", "127.0.0.1", "::1"}


def database_url() -> URL:
    """Return and validate the configured PostgreSQL URL."""

    url = make_url(get_settings().database_url)
    if not url.drivername.startswith("postgresql"):
        raise RuntimeError("The database backup tools require PostgreSQL.")
    if not url.database:
        raise RuntimeError("DATABASE_URL must contain a database name.")
    return url


def find_postgres_tool(name: str) -> Path:
    """Locate a PostgreSQL CLI tool on PATH or in common Windows locations."""

    executable_name = f"{name}.exe" if os.name == "nt" else name
    path_from_environment = shutil.which(executable_name)
    if path_from_environment:
        return Path(path_from_environment)

    if os.name == "nt":
        program_files = Path(os.environ.get("ProgramFiles", r"C:\Program Files"))
        postgres_root = program_files / "PostgreSQL"
        if postgres_root.exists():
            candidates = sorted(
                postgres_root.glob(f"*/bin/{executable_name}"),
                reverse=True,
            )
            if candidates:
                return candidates[0]

    raise RuntimeError(
        f"{executable_name} was not found. Install PostgreSQL client tools "
        "or add their bin directory to PATH."
    )


def postgres_environment(url: URL) -> dict[str, str]:
    """Build a child-process environment without exposing the password in args."""

    environment = os.environ.copy()
    if url.password:
        environment["PGPASSWORD"] = url.password
    return environment


def connection_arguments(url: URL) -> list[str]:
    """Build common PostgreSQL CLI connection arguments."""

    arguments: list[str] = []
    if url.host:
        arguments.extend(["--host", url.host])
    if url.port:
        arguments.extend(["--port", str(url.port)])
    if url.username:
        arguments.extend(["--username", url.username])
    return arguments
