"""Sync shared Szolnok weather forecast cache."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from app.modules.weather.application.commands.backfill_weather import (
    WeatherValidationError,
)
from app.modules.weather.application.commands.sync_shared_weather import (
    SHARED_WEATHER_LATITUDE,
    SHARED_WEATHER_LOCATION_NAME,
    SHARED_WEATHER_LONGITUDE,
    SHARED_WEATHER_PROVIDER,
    SHARED_WEATHER_TIMEZONE,
)
from app.modules.weather.application.services.weather_provider import WeatherProvider
from app.modules.weather.domain.entities.weather import (
    NewWeatherForecastHourly,
    NewWeatherLocation,
    WeatherLocation,
)
from app.modules.weather.domain.repositories.weather_repository import WeatherRepository


@dataclass(frozen=True, slots=True)
class WeatherForecastSyncSummary:
    """Result of syncing the shared forecast cache."""

    weather_location: WeatherLocation
    provider: str
    forecast_days: int
    requested_hours: int
    created_count: int
    updated_count: int


@dataclass(slots=True)
class SyncSharedWeatherForecastCommand:
    """Cache hourly forecast for the common Szolnok weather location."""

    repository: WeatherRepository
    provider: WeatherProvider

    def execute(self, *, forecast_days: int = 7) -> WeatherForecastSyncSummary:
        if forecast_days < 1 or forecast_days > 16:
            raise WeatherValidationError("Forecast sync can cover 1 to 16 days.")

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
        fetched = self.provider.fetch_hourly_forecast(
            latitude=weather_location.latitude,
            longitude=weather_location.longitude,
            timezone_name=weather_location.timezone,
            forecast_days=forecast_days,
        )
        run_at = datetime.now(timezone.utc)
        forecasts = [
            NewWeatherForecastHourly(
                weather_location_id=weather_location.id,
                forecasted_at=item.forecasted_at,
                provider=SHARED_WEATHER_PROVIDER,
                provider_model=item.provider_model,
                forecast_run_at=item.forecast_run_at or run_at,
                horizon_hours=_horizon_hours(
                    forecast_run_at=item.forecast_run_at or run_at,
                    forecasted_at=item.forecasted_at,
                ),
                weather_code=item.weather_code,
                weather_condition=item.weather_condition,
                temperature_c=item.temperature_c,
                apparent_temperature_c=item.apparent_temperature_c,
                relative_humidity_percent=item.relative_humidity_percent,
                precipitation_mm=item.precipitation_mm,
                rain_mm=item.rain_mm,
                snowfall_cm=item.snowfall_cm,
                cloud_cover_percent=item.cloud_cover_percent,
                wind_speed_kmh=item.wind_speed_kmh,
                wind_gust_kmh=item.wind_gust_kmh,
                pressure_hpa=item.pressure_hpa,
                source_payload=item.source_payload,
            )
            for item in fetched
        ]
        created_count, updated_count = self.repository.save_forecasts(forecasts)
        return WeatherForecastSyncSummary(
            weather_location=weather_location,
            provider=SHARED_WEATHER_PROVIDER,
            forecast_days=forecast_days,
            requested_hours=len(forecasts),
            created_count=created_count,
            updated_count=updated_count,
        )


def _horizon_hours(*, forecast_run_at: datetime, forecasted_at: datetime) -> int:
    return max(int((forecasted_at - forecast_run_at).total_seconds() // 3600), 0)


__all__ = ["SyncSharedWeatherForecastCommand", "WeatherForecastSyncSummary"]
