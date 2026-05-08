"""Weather domain entities."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class WeatherLocation:
    """One cached weather lookup point for a business unit."""

    id: uuid.UUID
    business_unit_id: uuid.UUID | None
    location_id: uuid.UUID | None
    scope: str
    name: str
    latitude: Decimal
    longitude: Decimal
    timezone: str
    provider: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class WeatherObservationHourly:
    """One hourly weather observation used as an analytics dimension."""

    id: uuid.UUID
    weather_location_id: uuid.UUID
    observed_at: datetime
    provider: str
    provider_model: str | None
    weather_code: int | None
    weather_condition: str
    temperature_c: Decimal | None
    apparent_temperature_c: Decimal | None
    relative_humidity_percent: Decimal | None
    precipitation_mm: Decimal | None
    rain_mm: Decimal | None
    snowfall_cm: Decimal | None
    cloud_cover_percent: Decimal | None
    wind_speed_kmh: Decimal | None
    wind_gust_kmh: Decimal | None
    pressure_hpa: Decimal | None
    source_payload: dict[str, object] | None
    fetched_at: datetime
    created_at: datetime


@dataclass(frozen=True, slots=True)
class WeatherForecastHourly:
    """One cached hourly weather forecast used for planning and prediction."""

    id: uuid.UUID
    weather_location_id: uuid.UUID
    forecasted_at: datetime
    provider: str
    provider_model: str | None
    forecast_run_at: datetime | None
    horizon_hours: int | None
    weather_code: int | None
    weather_condition: str
    temperature_c: Decimal | None
    apparent_temperature_c: Decimal | None
    relative_humidity_percent: Decimal | None
    precipitation_mm: Decimal | None
    rain_mm: Decimal | None
    snowfall_cm: Decimal | None
    cloud_cover_percent: Decimal | None
    wind_speed_kmh: Decimal | None
    wind_gust_kmh: Decimal | None
    pressure_hpa: Decimal | None
    source_payload: dict[str, object] | None
    fetched_at: datetime
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class NewWeatherLocation:
    """Draft weather location before persistence."""

    business_unit_id: uuid.UUID | None
    location_id: uuid.UUID | None
    scope: str
    name: str
    latitude: Decimal
    longitude: Decimal
    timezone: str
    provider: str
    is_active: bool


@dataclass(frozen=True, slots=True)
class NewWeatherObservationHourly:
    """Draft hourly observation before persistence."""

    weather_location_id: uuid.UUID
    observed_at: datetime
    provider: str
    provider_model: str | None
    weather_code: int | None
    weather_condition: str
    temperature_c: Decimal | None
    apparent_temperature_c: Decimal | None
    relative_humidity_percent: Decimal | None
    precipitation_mm: Decimal | None
    rain_mm: Decimal | None
    snowfall_cm: Decimal | None
    cloud_cover_percent: Decimal | None
    wind_speed_kmh: Decimal | None
    wind_gust_kmh: Decimal | None
    pressure_hpa: Decimal | None
    source_payload: dict[str, object] | None


@dataclass(frozen=True, slots=True)
class NewWeatherForecastHourly:
    """Draft hourly forecast before persistence."""

    weather_location_id: uuid.UUID
    forecasted_at: datetime
    provider: str
    provider_model: str | None
    forecast_run_at: datetime | None
    horizon_hours: int | None
    weather_code: int | None
    weather_condition: str
    temperature_c: Decimal | None
    apparent_temperature_c: Decimal | None
    relative_humidity_percent: Decimal | None
    precipitation_mm: Decimal | None
    rain_mm: Decimal | None
    snowfall_cm: Decimal | None
    cloud_cover_percent: Decimal | None
    wind_speed_kmh: Decimal | None
    wind_gust_kmh: Decimal | None
    pressure_hpa: Decimal | None
    source_payload: dict[str, object] | None
