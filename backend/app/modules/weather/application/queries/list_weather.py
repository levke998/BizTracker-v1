"""Weather read-side queries."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from app.modules.weather.domain.entities.weather import (
    WeatherForecastHourly,
    WeatherLocation,
    WeatherObservationHourly,
)
from app.modules.weather.domain.repositories.weather_repository import WeatherRepository


@dataclass(slots=True)
class ListWeatherLocationsQuery:
    """Return configured weather locations."""

    repository: WeatherRepository

    def execute(
        self,
        *,
        business_unit_id: uuid.UUID | None = None,
        is_active: bool | None = None,
        limit: int = 100,
    ) -> list[WeatherLocation]:
        return self.repository.list_locations(
            business_unit_id=business_unit_id,
            is_active=is_active,
            limit=limit,
        )


@dataclass(slots=True)
class ListWeatherObservationsQuery:
    """Return cached hourly weather observations."""

    repository: WeatherRepository

    def execute(
        self,
        *,
        business_unit_id: uuid.UUID | None = None,
        weather_location_id: uuid.UUID | None = None,
        start_at: datetime | None = None,
        end_at: datetime | None = None,
        limit: int = 500,
    ) -> list[WeatherObservationHourly]:
        return self.repository.list_observations(
            business_unit_id=business_unit_id,
            weather_location_id=weather_location_id,
            start_at=start_at,
            end_at=end_at,
            limit=limit,
        )


@dataclass(slots=True)
class ListWeatherForecastsQuery:
    """Return cached hourly weather forecasts."""

    repository: WeatherRepository

    def execute(
        self,
        *,
        weather_location_id: uuid.UUID | None = None,
        start_at: datetime | None = None,
        end_at: datetime | None = None,
        limit: int = 500,
    ) -> list[WeatherForecastHourly]:
        return self.repository.list_forecasts(
            weather_location_id=weather_location_id,
            start_at=start_at,
            end_at=end_at,
            limit=limit,
        )
