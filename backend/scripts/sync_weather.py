"""Sync the shared Szolnok hourly weather cache.

Intended for manual runs or a lightweight OS scheduler.
"""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

from app.db.session import SessionLocal
from app.modules.weather.application.commands.backfill_weather import BackfillWeatherCommand
from app.modules.weather.application.commands.sync_shared_weather import SyncSharedWeatherCommand
from app.modules.weather.application.services.weather_provider import OpenMeteoWeatherProvider
from app.modules.weather.infrastructure.repositories.sqlalchemy_weather_repository import (
    SqlAlchemyWeatherRepository,
)
from scripts.weather_sync_utils import acquire_lock, release_lock

DEFAULT_LOCK_FILE = Path("storage/weather-sync.lock")


def _print_result(payload: dict[str, object], *, as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, ensure_ascii=False, default=str))
        return

    if payload.get("status") == "skipped":
        print("Shared Szolnok weather sync skipped")
        print(f"Reason: {payload.get('reason')}")
        return

    print("Shared Szolnok weather sync completed")
    print(f"Range: {payload['start_date']} - {payload['end_date']}")
    print(f"Requested hours: {payload['requested_hours']}")
    print(f"Created: {payload['created_count']}")
    print(f"Updated: {payload['updated_count']}")
    print(f"Skipped: {payload['skipped_count']}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--days-back",
        type=int,
        default=2,
        help="Sync today and this many previous days. Default: 2.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print a single JSON line for scheduler logs.",
    )
    parser.add_argument(
        "--lock-file",
        default=str(DEFAULT_LOCK_FILE),
        help="Path to a lock file that prevents overlapping scheduler runs.",
    )
    parser.add_argument(
        "--lock-stale-minutes",
        type=int,
        default=90,
        help="Treat an existing lock as stale after this many minutes. Default: 90.",
    )
    args = parser.parse_args()

    lock_file = Path(args.lock_file)
    if not acquire_lock(lock_file, stale_after_minutes=args.lock_stale_minutes):
        _print_result(
            {
                "status": "skipped",
                "reason": "Another shared Szolnok weather sync appears to be running.",
                "lock_file": str(lock_file),
            },
            as_json=args.json,
        )
        return

    try:
        with SessionLocal() as session:
            repository = SqlAlchemyWeatherRepository(session)
            provider = OpenMeteoWeatherProvider()
            command = SyncSharedWeatherCommand(
                backfill_command=BackfillWeatherCommand(
                    repository=repository,
                    provider=provider,
                )
            )
            result = command.execute(days_back=args.days_back)
    finally:
        release_lock(lock_file)

    _print_result(
        {
            "status": "completed",
            "start_date": result.start_date.isoformat(),
            "end_date": result.end_date.isoformat(),
            "requested_hours": result.requested_hours,
            "created_count": result.created_count,
            "updated_count": result.updated_count,
            "skipped_count": result.skipped_count,
            "weather_location_id": str(result.weather_location.id),
            "provider": result.provider,
            "synced_at": datetime.now(UTC).isoformat(),
        },
        as_json=args.json,
    )


if __name__ == "__main__":
    main()
