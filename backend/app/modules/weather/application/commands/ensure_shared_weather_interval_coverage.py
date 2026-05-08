"""Ensure shared weather cache coverage for a concrete time interval."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from app.modules.weather.application.commands.backfill_weather import (
    BackfillWeatherCommand,
    WeatherValidationError,
)
from app.modules.weather.application.commands.sync_shared_weather import (
    SHARED_WEATHER_LATITUDE,
    SHARED_WEATHER_LOCATION_NAME,
    SHARED_WEATHER_LONGITUDE,
    SHARED_WEATHER_PROVIDER,
    SHARED_WEATHER_TIMEZONE,
)
from app.modules.weather.domain.entities.weather import NewWeatherLocation
from app.modules.weather.domain.repositories.weather_repository import WeatherRepository


@dataclass(frozen=True, slots=True)
class SharedWeatherIntervalCoverageResult:
    """Weather coverage result for one shared Szolnok time interval."""

    status: str
    reason: str | None
    start_at: datetime
    end_at: datetime
    requested_hours: int
    cached_hours: int
    missing_hours: int
    backfill_attempted: bool
    created_count: int
    updated_count: int
    skipped_count: int


@dataclass(slots=True)
class EnsureSharedWeatherIntervalCoverageCommand:
    """Ensure the shared hourly Szolnok cache covers a concrete interval."""

    repository: WeatherRepository
    backfill_command: BackfillWeatherCommand

    def execute(
        self,
        *,
        start_at: datetime,
        end_at: datetime,
        now: datetime | None = None,
    ) -> SharedWeatherIntervalCoverageResult:
        zone = ZoneInfo(SHARED_WEATHER_TIMEZONE)
        normalized_start = _as_zone(start_at, zone)
        normalized_end = _as_zone(end_at, zone)
        if normalized_start > normalized_end:
            raise WeatherValidationError("Start time must be before or equal to end time.")

        local_now = _as_zone(now, zone) if now is not None else datetime.now(zone)
        if normalized_start > local_now:
            return SharedWeatherIntervalCoverageResult(
                status="skipped",
                reason="Jövőbeli idősávhoz historikus időjárás még nem készíthető.",
                start_at=normalized_start,
                end_at=normalized_end,
                requested_hours=0,
                cached_hours=0,
                missing_hours=0,
                backfill_attempted=False,
                created_count=0,
                updated_count=0,
                skipped_count=0,
            )

        observed_end = min(normalized_end, local_now)
        expected_hours = _expected_interval_hours(
            start_at=normalized_start,
            end_at=observed_end,
        )
        if not expected_hours:
            return SharedWeatherIntervalCoverageResult(
                status="skipped",
                reason="Az idősáv nem tartalmaz előkészíthető megfigyelési órát.",
                start_at=normalized_start,
                end_at=normalized_end,
                requested_hours=0,
                cached_hours=0,
                missing_hours=0,
                backfill_attempted=False,
                created_count=0,
                updated_count=0,
                skipped_count=0,
            )

        weather_location = self.repository.get_or_create_location(
            NewWeatherLocation(
                business_unit_id=None,
                location_id=None,
                scope="shared",
                name=SHARED_WEATHER_LOCATION_NAME,
                latitude=SHARED_WEATHER_LATITUDE,
                longitude=SHARED_WEATHER_LONGITUDE,
                timezone=SHARED_WEATHER_TIMEZONE,
                provider=SHARED_WEATHER_PROVIDER,
                is_active=True,
            )
        )
        existing_hours = self.repository.list_existing_observed_at(
            weather_location_id=weather_location.id,
            provider=SHARED_WEATHER_PROVIDER,
            start_at=min(expected_hours),
            end_at=max(expected_hours),
        )
        cached_interval_hours = existing_hours & expected_hours
        missing_hours = expected_hours - existing_hours
        if not missing_hours:
            return SharedWeatherIntervalCoverageResult(
                status="covered",
                reason=None,
                start_at=normalized_start,
                end_at=normalized_end,
                requested_hours=len(expected_hours),
                cached_hours=len(cached_interval_hours),
                missing_hours=0,
                backfill_attempted=False,
                created_count=0,
                updated_count=0,
                skipped_count=len(cached_interval_hours),
            )

        summary = self.backfill_command.execute(
            business_unit_id=None,
            scope="shared",
            name=SHARED_WEATHER_LOCATION_NAME,
            latitude=SHARED_WEATHER_LATITUDE,
            longitude=SHARED_WEATHER_LONGITUDE,
            start_date=normalized_start.date(),
            end_date=observed_end.date(),
            timezone_name=SHARED_WEATHER_TIMEZONE,
            provider_name=SHARED_WEATHER_PROVIDER,
        )
        refreshed_existing_hours = self.repository.list_existing_observed_at(
            weather_location_id=weather_location.id,
            provider=SHARED_WEATHER_PROVIDER,
            start_at=min(expected_hours),
            end_at=max(expected_hours),
        )
        refreshed_missing_hours = expected_hours - refreshed_existing_hours
        return SharedWeatherIntervalCoverageResult(
            status="backfilled",
            reason=None,
            start_at=normalized_start,
            end_at=normalized_end,
            requested_hours=len(expected_hours),
            cached_hours=len(refreshed_existing_hours & expected_hours),
            missing_hours=len(refreshed_missing_hours),
            backfill_attempted=True,
            created_count=summary.created_count,
            updated_count=summary.updated_count,
            skipped_count=summary.skipped_count,
        )


def _as_zone(value: datetime, zone: ZoneInfo) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=zone)
    return value.astimezone(zone)


def _expected_interval_hours(*, start_at: datetime, end_at: datetime) -> set[datetime]:
    current = start_at.replace(minute=0, second=0, microsecond=0)
    end = end_at.replace(minute=0, second=0, microsecond=0)
    hours: set[datetime] = set()
    while current <= end:
        hours.add(current.astimezone(timezone.utc))
        current += timedelta(hours=1)
    return hours


__all__ = [
    "EnsureSharedWeatherIntervalCoverageCommand",
    "SharedWeatherIntervalCoverageResult",
]
