"""Weather provider boundary and Open-Meteo implementation."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Protocol
from urllib.parse import urlencode
from urllib.request import urlopen
from zoneinfo import ZoneInfo


OPEN_METEO_HOURLY_FIELDS = (
    "temperature_2m",
    "apparent_temperature",
    "relative_humidity_2m",
    "precipitation",
    "rain",
    "snowfall",
    "weather_code",
    "cloud_cover",
    "wind_speed_10m",
    "wind_gusts_10m",
    "surface_pressure",
)


@dataclass(frozen=True, slots=True)
class FetchedWeatherObservation:
    """Provider-neutral hourly weather observation."""

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
class FetchedWeatherForecast:
    """Provider-neutral hourly weather forecast."""

    forecasted_at: datetime
    provider: str
    provider_model: str | None
    forecast_run_at: datetime | None
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


class WeatherProvider(Protocol):
    """External weather provider boundary."""

    provider_name: str

    def fetch_hourly(
        self,
        *,
        latitude: Decimal,
        longitude: Decimal,
        timezone_name: str,
        start_date: date,
        end_date: date,
    ) -> list[FetchedWeatherObservation]:
        """Fetch hourly observations for the inclusive date range."""

    def fetch_hourly_forecast(
        self,
        *,
        latitude: Decimal,
        longitude: Decimal,
        timezone_name: str,
        forecast_days: int,
    ) -> list[FetchedWeatherForecast]:
        """Fetch hourly forecast rows for the next forecast_days days."""


class OpenMeteoWeatherProvider:
    """Fetch historical hourly data from Open-Meteo archive API."""

    provider_name = "open_meteo"
    archive_base_url = "https://archive-api.open-meteo.com/v1/archive"
    forecast_base_url = "https://api.open-meteo.com/v1/forecast"

    def fetch_hourly(
        self,
        *,
        latitude: Decimal,
        longitude: Decimal,
        timezone_name: str,
        start_date: date,
        end_date: date,
    ) -> list[FetchedWeatherObservation]:
        query = urlencode(
            {
                "latitude": str(latitude),
                "longitude": str(longitude),
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "timezone": timezone_name,
                "hourly": ",".join(OPEN_METEO_HOURLY_FIELDS),
            }
        )
        base_url = self._select_base_url(end_date=end_date, timezone_name=timezone_name)
        with urlopen(f"{base_url}?{query}", timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
        return _parse_open_meteo_payload(
            payload,
            timezone_name=timezone_name,
            provider=self.provider_name,
        )

    def _select_base_url(self, *, end_date: date, timezone_name: str) -> str:
        local_today = datetime.now(ZoneInfo(timezone_name)).date()
        if end_date >= local_today:
            return self.forecast_base_url
        return self.archive_base_url

    def fetch_hourly_forecast(
        self,
        *,
        latitude: Decimal,
        longitude: Decimal,
        timezone_name: str,
        forecast_days: int,
    ) -> list[FetchedWeatherForecast]:
        query = urlencode(
            {
                "latitude": str(latitude),
                "longitude": str(longitude),
                "timezone": timezone_name,
                "forecast_days": forecast_days,
                "hourly": ",".join(OPEN_METEO_HOURLY_FIELDS),
            }
        )
        with urlopen(f"{self.forecast_base_url}?{query}", timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
        return _parse_open_meteo_forecast_payload(
            payload,
            timezone_name=timezone_name,
            provider=self.provider_name,
        )


def _parse_open_meteo_payload(
    payload: dict[str, object],
    *,
    timezone_name: str,
    provider: str,
) -> list[FetchedWeatherObservation]:
    hourly = payload.get("hourly")
    if not isinstance(hourly, dict):
        return []

    times = hourly.get("time")
    if not isinstance(times, list):
        return []

    local_zone = ZoneInfo(timezone_name)
    observations: list[FetchedWeatherObservation] = []
    for index, raw_time in enumerate(times):
        if not isinstance(raw_time, str):
            continue

        local_time = datetime.fromisoformat(raw_time).replace(tzinfo=local_zone)
        observed_at = local_time.astimezone(timezone.utc)
        weather_code = _optional_int(_hourly_value(hourly, "weather_code", index))
        wind_speed = _optional_decimal(_hourly_value(hourly, "wind_speed_10m", index))
        wind_gust = _optional_decimal(_hourly_value(hourly, "wind_gusts_10m", index))

        observations.append(
            FetchedWeatherObservation(
                observed_at=observed_at,
                provider=provider,
                provider_model="open-meteo-archive",
                weather_code=weather_code,
                weather_condition=map_weather_condition(
                    weather_code,
                    wind_speed_kmh=wind_speed,
                    wind_gust_kmh=wind_gust,
                ),
                temperature_c=_optional_decimal(_hourly_value(hourly, "temperature_2m", index)),
                apparent_temperature_c=_optional_decimal(
                    _hourly_value(hourly, "apparent_temperature", index)
                ),
                relative_humidity_percent=_optional_decimal(
                    _hourly_value(hourly, "relative_humidity_2m", index)
                ),
                precipitation_mm=_optional_decimal(_hourly_value(hourly, "precipitation", index)),
                rain_mm=_optional_decimal(_hourly_value(hourly, "rain", index)),
                snowfall_cm=_optional_decimal(_hourly_value(hourly, "snowfall", index)),
                cloud_cover_percent=_optional_decimal(_hourly_value(hourly, "cloud_cover", index)),
                wind_speed_kmh=wind_speed,
                wind_gust_kmh=wind_gust,
                pressure_hpa=_optional_decimal(_hourly_value(hourly, "surface_pressure", index)),
                source_payload={
                    "local_time": raw_time,
                    "provider_timezone": timezone_name,
                    "source": "open_meteo_archive",
                },
            )
        )
    return observations


def _parse_open_meteo_forecast_payload(
    payload: dict[str, object],
    *,
    timezone_name: str,
    provider: str,
) -> list[FetchedWeatherForecast]:
    hourly = payload.get("hourly")
    if not isinstance(hourly, dict):
        return []

    times = hourly.get("time")
    if not isinstance(times, list):
        return []

    local_zone = ZoneInfo(timezone_name)
    run_at = datetime.now(timezone.utc)
    forecasts: list[FetchedWeatherForecast] = []
    for index, raw_time in enumerate(times):
        if not isinstance(raw_time, str):
            continue

        local_time = datetime.fromisoformat(raw_time).replace(tzinfo=local_zone)
        forecasted_at = local_time.astimezone(timezone.utc)
        weather_code = _optional_int(_hourly_value(hourly, "weather_code", index))
        wind_speed = _optional_decimal(_hourly_value(hourly, "wind_speed_10m", index))
        wind_gust = _optional_decimal(_hourly_value(hourly, "wind_gusts_10m", index))

        forecasts.append(
            FetchedWeatherForecast(
                forecasted_at=forecasted_at,
                provider=provider,
                provider_model="open-meteo-forecast",
                forecast_run_at=run_at,
                weather_code=weather_code,
                weather_condition=map_weather_condition(
                    weather_code,
                    wind_speed_kmh=wind_speed,
                    wind_gust_kmh=wind_gust,
                ),
                temperature_c=_optional_decimal(_hourly_value(hourly, "temperature_2m", index)),
                apparent_temperature_c=_optional_decimal(
                    _hourly_value(hourly, "apparent_temperature", index)
                ),
                relative_humidity_percent=_optional_decimal(
                    _hourly_value(hourly, "relative_humidity_2m", index)
                ),
                precipitation_mm=_optional_decimal(_hourly_value(hourly, "precipitation", index)),
                rain_mm=_optional_decimal(_hourly_value(hourly, "rain", index)),
                snowfall_cm=_optional_decimal(_hourly_value(hourly, "snowfall", index)),
                cloud_cover_percent=_optional_decimal(_hourly_value(hourly, "cloud_cover", index)),
                wind_speed_kmh=wind_speed,
                wind_gust_kmh=wind_gust,
                pressure_hpa=_optional_decimal(_hourly_value(hourly, "surface_pressure", index)),
                source_payload={
                    "local_time": raw_time,
                    "provider_timezone": timezone_name,
                    "source": "open_meteo_forecast",
                },
            )
        )
    return forecasts


def map_weather_condition(
    weather_code: int | None,
    *,
    wind_speed_kmh: Decimal | None = None,
    wind_gust_kmh: Decimal | None = None,
) -> str:
    """Map WMO weather codes into Hungarian business analytics buckets."""

    if weather_code in {95, 96, 99}:
        return "viharos"
    if weather_code in {71, 73, 75, 77, 85, 86}:
        return "havas"
    if weather_code in {51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82}:
        return "esos"
    if weather_code in {45, 48}:
        return "kodos"
    if _is_windy(wind_speed_kmh=wind_speed_kmh, wind_gust_kmh=wind_gust_kmh):
        return "szeles"
    if weather_code == 0:
        return "napos"
    if weather_code in {1, 2}:
        return "reszben_felhos"
    if weather_code == 3:
        return "borult"
    return "ismeretlen"


def _is_windy(
    *,
    wind_speed_kmh: Decimal | None,
    wind_gust_kmh: Decimal | None,
) -> bool:
    return bool(
        (wind_speed_kmh is not None and wind_speed_kmh >= Decimal("35"))
        or (wind_gust_kmh is not None and wind_gust_kmh >= Decimal("50"))
    )


def _hourly_value(hourly: dict[object, object], field: str, index: int) -> object:
    values = hourly.get(field)
    if not isinstance(values, list) or index >= len(values):
        return None
    return values[index]


def _optional_decimal(value: object) -> Decimal | None:
    if value is None:
        return None
    return Decimal(str(value))


def _optional_int(value: object) -> int | None:
    if value is None:
        return None
    return int(value)
