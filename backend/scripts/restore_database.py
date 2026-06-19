"""Restore a BizTracker PostgreSQL dump with explicit safety checks."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

from scripts.database_tools import (
    LOCAL_DATABASE_HOSTS,
    connection_arguments,
    database_url,
    find_postgres_tool,
    postgres_environment,
)


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""

    parser = argparse.ArgumentParser(
        description=(
            "Replace the configured local database content from a PostgreSQL dump."
        ),
    )
    parser.add_argument("dump", type=Path, help="Path to a custom-format .dump file")
    parser.add_argument(
        "--confirm-database",
        required=True,
        help="Must exactly match the database name from DATABASE_URL.",
    )
    parser.add_argument(
        "--allow-remote",
        action="store_true",
        help="Allow restoring to a non-local host. Use only intentionally.",
    )
    return parser.parse_args()


def main() -> None:
    """Restore the configured database after validating the target."""

    args = parse_args()
    dump_path = args.dump.expanduser().resolve()
    if not dump_path.is_file():
        raise RuntimeError(f"Dump file does not exist: {dump_path}")

    url = database_url()
    if args.confirm_database != url.database:
        raise RuntimeError(
            "--confirm-database must exactly match the configured database name "
            f"({url.database})."
        )

    host = url.host or "localhost"
    if host not in LOCAL_DATABASE_HOSTS and not args.allow_remote:
        raise RuntimeError(
            f"Refusing to restore remote host '{host}'. "
            "Pass --allow-remote only if this destructive action is intentional."
        )

    pg_restore = find_postgres_tool("pg_restore")
    command = [
        str(pg_restore),
        *connection_arguments(url),
        "--dbname",
        url.database,
        "--clean",
        "--if-exists",
        "--no-owner",
        "--no-privileges",
        "--exit-on-error",
        str(dump_path),
    ]

    subprocess.run(
        command,
        check=True,
        env=postgres_environment(url),
    )
    print(f"Database restored from: {dump_path}")
    print("Run 'python -m alembic upgrade head' before starting development.")


if __name__ == "__main__":
    main()
