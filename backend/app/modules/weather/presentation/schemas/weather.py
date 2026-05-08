"""Weather API schemas."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class WeatherBackfillRequest(BaseModel):
    """Payload for caching hourly weather data."""

    business_unit_id: uuid.UUID | None = None
    location_id: uuid.UUID | None = None
    scope: str = Field(default="business_unit", max_length=30)
    name: str = Field(min_length=1, max_length=150)
    latitude: Decimal = Field(ge=Decimal("-90"), le=Decimal("90"))
    longitude: Decimal = Field(ge=Decimal("-180"), le=Decimal("180"))
    start_date: date
    end_date: date
    timezone_name: str = Field(default="Europe/Budapest", max_length=80)
    provider_name: str = Field(default="open_meteo", max_length=50)


class WeatherLocationResponse(BaseModel):
    """Weather location read model."""

    model_config = ConfigDict(from_attributes=True)

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


class WeatherBackfillResponse(BaseModel):
    """Weather backfill result."""

    model_config = ConfigDict(from_attributes=True)

    weather_location: WeatherLocationResponse
    provider: str
    start_date: date
    end_date: date
    requested_hours: int
    created_count: int
    updated_count: int
    skipped_count: int


class WeatherForecastSyncResponse(BaseModel):
    """Weather forecast sync result."""

    model_config = ConfigDict(from_attributes=True)

    weather_location: WeatherLocationResponse
    provider: str
    forecast_days: int
    requested_hours: int
    created_count: int
    updated_count: int


class ImportBatchWeatherRecommendationResponse(BaseModel):
    """Weather preparation recommendation for one import batch."""

    model_config = ConfigDict(from_attributes=True)

    batch_id: uuid.UUID
    business_unit_id: uuid.UUID
    business_unit_code: str
    business_unit_name: str
    import_type: str
    status: str
    parsed_rows: int
    can_backfill: bool
    reason: str | None
    first_sale_at: datetime | None
    last_sale_at: datetime | None
    start_date: date | None
    end_date: date | None
    timezone_name: str
    suggested_location_name: str
    latitude: Decimal
    longitude: Decimal
    provider_name: str
    requested_hours: int
    cached_hours: int
    missing_hours: int


class ImportBatchWeatherCoverageResponse(BaseModel):
    """Weather coverage orchestration result for one import batch."""

    model_config = ConfigDict(from_attributes=True)

    batch_id: uuid.UUID
    status: str
    reason: str | None
    start_date: date | None
    end_date: date | None
    requested_hours: int
    cached_hours: int
    missing_hours: int
    backfill_attempted: bool
    created_count: int
    updated_count: int
    skipped_count: int


class SharedWeatherIntervalCoverageResponse(BaseModel):
    """Weather coverage orchestration result for a shared time interval."""

    model_config = ConfigDict(from_attributes=True)

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


class WeatherObservationResponse(BaseModel):
    """Cached hourly weather observation read model."""

    model_config = ConfigDict(from_attributes=True)

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


class WeatherForecastResponse(BaseModel):
    """Cached hourly forecast read model."""

    model_config = ConfigDict(from_attributes=True)

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
