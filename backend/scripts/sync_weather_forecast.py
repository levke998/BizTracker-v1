"""Sync the shared Szolnok hourly weather forecast cache.

Intended for manual runs or a lightweight OS scheduler.
"""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

from app.db.session import SessionLocal
from app.modules.weather.application.commands.sync_shared_weather_forecast import (
    SyncSharedWeatherForecastCommand,
)
from app.modules.weather.application.services.weather_provider import (
    OpenMeteoWeatherProvider,
)
from app.modules.weather.infrastructure.repositories.sqlalchemy_weather_repository import (
    SqlAlchemyWeatherRepository,
)
from scripts.weather_sync_utils import acquire_lock, release_lock

DEFAULT_LOCK_FILE = Path("storage/weather-forecast-sync.lock")


def _print_result(payload: dict[str, object], *, as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, ensure_ascii=False, default=str))
        return

    if payload.get("status") == "skipped":
        print("Shared Szolnok weather forecast sync skipped")
        print(f"Reason: {payload.get('reason')}")
        return

    print("Shared Szolnok weather forecast sync completed")
    print(f"Forecast days: {payload['forecast_days']}")
    print(f"Requested hours: {payload['requested_hours']}")
    print(f"Created: {payload['created_count']}")
    print(f"Updated: {payload['updated_count']}")
    print(f"Skipped: {payload['skipped_count']}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--forecast-days",
        type=int,
        default=7,
        help="Sync this many forecast days. Open-Meteo supports up to 16. Default: 7.",
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
        default=45,
        help="Treat an existing lock as stale after this many minutes. Default: 45.",
    )
    args = parser.parse_args()

    lock_file = Path(args.lock_file)
    if not acquire_lock(lock_file, stale_after_minutes=args.lock_stale_minutes):
        _print_result(
            {
                "status": "skipped",
                "reason": "Another shared Szolnok weather forecast sync appears to be running.",
                "lock_file": str(lock_file),
            },
            as_json=args.json,
        )
        return

    try:
        with SessionLocal() as session:
            repository = SqlAlchemyWeatherRepository(session)
            provider = OpenMeteoWeatherProvider()
            command = SyncSharedWeatherForecastCommand(
                repository=repository,
                provider=provider,
            )
            result = command.execute(forecast_days=args.forecast_days)
    finally:
        release_lock(lock_file)

    _print_result(
        {
            "status": "completed",
            "forecast_days": result.forecast_days,
            "requested_hours": result.requested_hours,
            "created_count": result.created_count,
            "updated_count": result.updated_count,
            "skipped_count": 0,
            "weather_location_id": str(result.weather_location.id),
            "provider": result.provider,
            "synced_at": datetime.now(UTC).isoformat(),
        },
        as_json=args.json,
    )


if __name__ == "__main__":
    main()
