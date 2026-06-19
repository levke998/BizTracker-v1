"""Create a portable custom-format dump of the configured BizTracker database."""

from __future__ import annotations

import argparse
import subprocess
from datetime import datetime
from pathlib import Path

from scripts.database_tools import (
    connection_arguments,
    database_url,
    find_postgres_tool,
    postgres_environment,
)

BACKEND_ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""

    timestamp = datetime.now().astimezone().strftime("%Y%m%d-%H%M%S")
    default_output = BACKEND_ROOT / "backups" / f"biztracker-{timestamp}.dump"

    parser = argparse.ArgumentParser(
        description="Create a PostgreSQL dump using backend/.env.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=default_output,
        help=f"Output dump path (default: {default_output})",
    )
    return parser.parse_args()


def main() -> None:
    """Create the database dump."""

    args = parse_args()
    output_path = args.output.expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    url = database_url()
    pg_dump = find_postgres_tool("pg_dump")
    command = [
        str(pg_dump),
        *connection_arguments(url),
        "--format",
        "custom",
        "--no-owner",
        "--no-privileges",
        "--file",
        str(output_path),
        url.database,
    ]

    subprocess.run(
        command,
        check=True,
        env=postgres_environment(url),
    )
    print(f"Database backup created: {output_path}")
    print("Keep this file outside Git and transfer it through a secure channel.")


if __name__ == "__main__":
    main()
