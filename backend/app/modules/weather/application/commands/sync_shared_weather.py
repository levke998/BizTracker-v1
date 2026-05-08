"""Automated shared Szolnok weather sync."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

from app.modules.weather.application.commands.backfill_weather import (
    BackfillWeatherCommand,
    WeatherBackfillSummary,
    WeatherValidationError,
)

SHARED_WEATHER_LOCATION_NAME = "Szolnok közös időjárás"
SHARED_WEATHER_LATITUDE = Decimal("47.174961")
SHARED_WEATHER_LONGITUDE = Decimal("20.176517")
SHARED_WEATHER_TIMEZONE = "Europe/Budapest"
SHARED_WEATHER_PROVIDER = "open_meteo"


@dataclass(slots=True)
class SyncSharedWeatherCommand:
    """Sync the common hourly Szolnok weather cache used by both businesses."""

    backfill_command: BackfillWeatherCommand

    def execute(
        self,
        *,
        days_back: int = 2,
        end_date: date | None = None,
    ) -> WeatherBackfillSummary:
        if days_back < 0 or days_back > 30:
            raise WeatherValidationError("Shared weather sync can cover 0 to 30 days back.")

        local_today = date.today()
        if end_date is None:
            end_date = local_today
        start_date = end_date - timedelta(days=days_back)
        ZoneInfo(SHARED_WEATHER_TIMEZONE)

        return self.backfill_command.execute(
            business_unit_id=None,
            scope="shared",
            name=SHARED_WEATHER_LOCATION_NAME,
            latitude=SHARED_WEATHER_LATITUDE,
            longitude=SHARED_WEATHER_LONGITUDE,
            start_date=start_date,
            end_date=end_date,
            timezone_name=SHARED_WEATHER_TIMEZONE,
            provider_name=SHARED_WEATHER_PROVIDER,
        )
