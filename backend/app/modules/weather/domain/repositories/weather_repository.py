"""Weather repository contracts."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Protocol

from app.modules.weather.domain.entities.weather import (
    NewWeatherForecastHourly,
    NewWeatherLocation,
    NewWeatherObservationHourly,
    WeatherForecastHourly,
    WeatherLocation,
    WeatherObservationHourly,
)


class WeatherRepository(Protocol):
    """Persistence boundary for cached weather analytics data."""

    def business_unit_exists(self, business_unit_id: uuid.UUID) -> bool:
        """Return whether the business unit exists."""

    def location_belongs_to_business_unit(
        self,
        *,
        location_id: uuid.UUID,
        business_unit_id: uuid.UUID,
    ) -> bool:
        """Return whether a master-data location belongs to the business unit."""

    def get_or_create_location(self, location: NewWeatherLocation) -> WeatherLocation:
        """Return an existing weather location or create it."""

    def list_locations(
        self,
        *,
        business_unit_id: uuid.UUID | None = None,
        is_active: bool | None = None,
        limit: int = 100,
    ) -> list[WeatherLocation]:
        """Return weather locations."""

    def list_existing_observed_at(
        self,
        *,
        weather_location_id: uuid.UUID,
        provider: str,
        start_at: datetime,
        end_at: datetime,
    ) -> set[datetime]:
        """Return cached hourly timestamps for one location and provider."""

    def save_observations(
        self,
        observations: list[NewWeatherObservationHourly],
    ) -> tuple[int, int]:
        """Persist observations and return created/updated counts."""

    def save_forecasts(
        self,
        forecasts: list[NewWeatherForecastHourly],
    ) -> tuple[int, int]:
        """Persist forecast rows and return created/updated counts."""

    def list_observations(
        self,
        *,
        business_unit_id: uuid.UUID | None = None,
        weather_location_id: uuid.UUID | None = None,
        start_at: datetime | None = None,
        end_at: datetime | None = None,
        limit: int = 500,
    ) -> list[WeatherObservationHourly]:
        """Return cached weather observations."""

    def list_forecasts(
        self,
        *,
        weather_location_id: uuid.UUID | None = None,
        start_at: datetime | None = None,
        end_at: datetime | None = None,
        limit: int = 500,
    ) -> list[WeatherForecastHourly]:
        """Return cached weather forecasts."""
