"""Backfill cached hourly weather observations."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.modules.weather.application.services.weather_provider import WeatherProvider
from app.modules.weather.domain.entities.weather import (
    NewWeatherLocation,
    NewWeatherObservationHourly,
    WeatherLocation,
)
from app.modules.weather.domain.repositories.weather_repository import WeatherRepository


class WeatherBusinessUnitNotFoundError(Exception):
    """Raised when the selected business unit does not exist."""


class WeatherLocationMismatchError(Exception):
    """Raised when the selected location does not belong to the business unit."""


class WeatherValidationError(Exception):
    """Raised when the weather request violates business rules."""


@dataclass(frozen=True, slots=True)
class WeatherBackfillSummary:
    """Result of a weather backfill operation."""

    weather_location: WeatherLocation
    provider: str
    start_date: date
    end_date: date
    requested_hours: int
    created_count: int
    updated_count: int
    skipped_count: int


@dataclass(slots=True)
class BackfillWeatherCommand:
    """Cache hourly weather data for a business unit and date range."""

    repository: WeatherRepository
    provider: WeatherProvider

    def execute(
        self,
        *,
        business_unit_id: uuid.UUID | None,
        name: str,
        latitude: Decimal,
        longitude: Decimal,
        start_date: date,
        end_date: date,
        timezone_name: str = "Europe/Budapest",
        location_id: uuid.UUID | None = None,
        scope: str = "business_unit",
        provider_name: str = "open_meteo",
    ) -> WeatherBackfillSummary:
        if provider_name != self.provider.provider_name:
            raise WeatherValidationError("Unsupported weather provider.")
        normalized_scope = scope.strip().lower()
        if normalized_scope not in {"business_unit", "shared"}:
            raise WeatherValidationError("Unsupported weather location scope.")
        if normalized_scope == "business_unit" and business_unit_id is None:
            raise WeatherValidationError(
                "Business unit is required for business-unit weather locations."
            )
        if normalized_scope == "shared" and location_id is not None:
            raise WeatherValidationError(
                "Shared weather locations cannot use a business-unit location."
            )
        if business_unit_id is not None and not self.repository.business_unit_exists(business_unit_id):
            raise WeatherBusinessUnitNotFoundError(
                f"Business unit {business_unit_id} was not found."
            )
        if (
            business_unit_id is not None
            and location_id is not None
            and not self.repository.location_belongs_to_business_unit(
                location_id=location_id,
                business_unit_id=business_unit_id,
            )
        ):
            raise WeatherLocationMismatchError(
                "The selected location does not belong to the business unit."
            )

        normalized_name = name.strip()
        if not normalized_name:
            raise WeatherValidationError("Weather location name is required.")
        if start_date > end_date:
            raise WeatherValidationError("Start date must be before or equal to end date.")
        if (end_date - start_date).days > 366:
            raise WeatherValidationError("Weather backfill can cover at most 367 days at once.")
        try:
            ZoneInfo(timezone_name)
        except ZoneInfoNotFoundError as exc:
            raise WeatherValidationError("Unknown weather timezone.") from exc

        weather_location = self.repository.get_or_create_location(
            NewWeatherLocation(
                business_unit_id=business_unit_id,
                location_id=location_id,
                scope=normalized_scope,
                name=normalized_name,
                latitude=latitude,
                longitude=longitude,
                timezone=timezone_name,
                provider=provider_name,
                is_active=True,
            )
        )
        expected_hours = _expected_observed_hours(
            start_date=start_date,
            end_date=end_date,
            timezone_name=timezone_name,
        )
        if not expected_hours:
            raise WeatherValidationError("Weather backfill range is empty.")

        existing_hours = self.repository.list_existing_observed_at(
            weather_location_id=weather_location.id,
            provider=provider_name,
            start_at=min(expected_hours),
            end_at=max(expected_hours),
        )
        missing_hours = expected_hours - existing_hours
        skipped_count = len(existing_hours & expected_hours)
        created_count = 0
        updated_count = 0

        if missing_hours:
            fetched = self.provider.fetch_hourly(
                latitude=weather_location.latitude,
                longitude=weather_location.longitude,
                timezone_name=weather_location.timezone,
                start_date=start_date,
                end_date=end_date,
            )
            observations = []
            seen_observed_at: set[datetime] = set()
            for observation in fetched:
                if observation.observed_at not in missing_hours:
                    continue
                if observation.observed_at in seen_observed_at:
                    continue
                seen_observed_at.add(observation.observed_at)
                observations.append(
                    NewWeatherObservationHourly(
                        weather_location_id=weather_location.id,
                        observed_at=observation.observed_at,
                        provider=provider_name,
                        provider_model=observation.provider_model,
                        weather_code=observation.weather_code,
                        weather_condition=observation.weather_condition,
                        temperature_c=observation.temperature_c,
                        apparent_temperature_c=observation.apparent_temperature_c,
                        relative_humidity_percent=observation.relative_humidity_percent,
                        precipitation_mm=observation.precipitation_mm,
                        rain_mm=observation.rain_mm,
                        snowfall_cm=observation.snowfall_cm,
                        cloud_cover_percent=observation.cloud_cover_percent,
                        wind_speed_kmh=observation.wind_speed_kmh,
                        wind_gust_kmh=observation.wind_gust_kmh,
                        pressure_hpa=observation.pressure_hpa,
                        source_payload=observation.source_payload,
                    )
                )
            created_count, updated_count = self.repository.save_observations(observations)

        return WeatherBackfillSummary(
            weather_location=weather_location,
            provider=provider_name,
            start_date=start_date,
            end_date=end_date,
            requested_hours=len(expected_hours),
            created_count=created_count,
            updated_count=updated_count,
            skipped_count=skipped_count,
        )


def _expected_observed_hours(
    *,
    start_date: date,
    end_date: date,
    timezone_name: str,
) -> set[datetime]:
    zone = ZoneInfo(timezone_name)
    current = datetime.combine(start_date, time.min, tzinfo=zone)
    end = datetime.combine(end_date, time(hour=23), tzinfo=zone)
    observed_hours: set[datetime] = set()
    while current <= end:
        observed_hours.add(current.astimezone(timezone.utc))
        current += timedelta(hours=1)
    return observed_hours
