"""Shared forecast cache access and deterministic forecast aggregation rules."""

from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.analytics.infrastructure.repositories.weather_analytics_reader import (
    hour_start_utc,
)
from app.modules.weather.infrastructure.orm.weather_model import (
    WeatherForecastHourlyModel,
    WeatherLocationModel,
)


class ForecastAnalyticsReader:
    """Read shared forecast rows and prepare reusable analytics aggregates."""

    def __init__(
        self,
        session: Session,
        *,
        time_zone: ZoneInfo,
        location_name: str,
        provider: str,
    ) -> None:
        self._session = session
        self._time_zone = time_zone
        self._location_name = location_name
        self._provider = provider

    def list_forecasts(
        self,
        *,
        start_at: datetime,
        end_at: datetime,
    ) -> list[WeatherForecastHourlyModel]:
        statement = (
            select(WeatherForecastHourlyModel)
            .join(
                WeatherLocationModel,
                WeatherForecastHourlyModel.weather_location_id
                == WeatherLocationModel.id,
            )
            .where(WeatherLocationModel.scope == "shared")
            .where(WeatherLocationModel.name == self._location_name)
            .where(WeatherLocationModel.provider == self._provider)
            .where(WeatherForecastHourlyModel.provider == self._provider)
            .where(WeatherForecastHourlyModel.forecasted_at >= hour_start_utc(start_at))
            .where(WeatherForecastHourlyModel.forecasted_at <= hour_start_utc(end_at))
            .order_by(WeatherForecastHourlyModel.forecasted_at.asc())
        )
        return list(self._session.scalars(statement).all())

    def aggregate_days(
        self,
        forecasts: list[WeatherForecastHourlyModel],
    ) -> dict[date, dict[str, Any]]:
        forecast_days: dict[date, dict[str, Any]] = defaultdict(
            lambda: {
                "hour_count": 0,
                "temperatures": [],
                "precipitation_sum": Decimal("0"),
                "condition_counts": defaultdict(int),
                "latest_forecast_run_at": None,
            }
        )
        for forecast in forecasts:
            local_date = forecast.forecasted_at.astimezone(self._time_zone).date()
            values = forecast_days[local_date]
            values["hour_count"] += 1
            if forecast.temperature_c is not None:
                values["temperatures"].append(Decimal(forecast.temperature_c))
            values["precipitation_sum"] += forecast_precipitation(forecast)
            values["condition_counts"][forecast_condition_band(forecast)] += 1
            latest = values["latest_forecast_run_at"]
            if latest is None or (
                forecast.forecast_run_at is not None
                and forecast.forecast_run_at > latest
            ):
                values["latest_forecast_run_at"] = forecast.forecast_run_at
        return forecast_days

    def aggregate_time_windows(
        self,
        forecasts: list[WeatherForecastHourlyModel],
    ) -> dict[tuple[date, str], dict[str, Any]]:
        windows: dict[tuple[date, str], dict[str, Any]] = defaultdict(
            lambda: {"temperatures": [], "condition_counts": defaultdict(int)}
        )
        for forecast in forecasts:
            local_value = forecast.forecasted_at.astimezone(self._time_zone)
            key = (local_value.date(), time_window_label(local_value.hour))
            if forecast.temperature_c is not None:
                windows[key]["temperatures"].append(Decimal(forecast.temperature_c))
            windows[key]["condition_counts"][forecast_condition_band(forecast)] += 1
        return windows

    @staticmethod
    def event_window(
        *,
        starts_at: datetime,
        ends_at: datetime,
        forecasts_by_hour: dict[datetime, WeatherForecastHourlyModel],
    ) -> list[WeatherForecastHourlyModel]:
        current = hour_start_utc(starts_at)
        end_hour = hour_start_utc(ends_at)
        rows: list[WeatherForecastHourlyModel] = []
        while current <= end_hour:
            forecast = forecasts_by_hour.get(current)
            if forecast is not None:
                rows.append(forecast)
            current += timedelta(hours=1)
        return rows


def forecast_precipitation(forecast: WeatherForecastHourlyModel) -> Decimal:
    values = (
        forecast.precipitation_mm,
        forecast.rain_mm,
        forecast.snowfall_cm,
    )
    return max((Decimal(value or 0) for value in values), default=Decimal("0"))


def forecast_condition_band(forecast: WeatherForecastHourlyModel) -> str:
    if forecast_precipitation(forecast) > Decimal("0"):
        return "csapadekos"
    cloud_cover = Decimal(forecast.cloud_cover_percent or 0)
    if cloud_cover >= Decimal("70"):
        return "borult"
    if cloud_cover >= Decimal("35"):
        return "reszben_felhos"
    return "napos_szaraz"


def time_window_label(hour: int) -> str:
    if 6 <= hour < 10:
        return "Reggel"
    if 10 <= hour < 13:
        return "Délelőtt"
    if 13 <= hour < 17:
        return "Délután"
    if 17 <= hour < 22:
        return "Este"
    return "Zárás körül"


def time_window_hours(time_window: str) -> tuple[int, int]:
    windows = {
        "Reggel": (6, 10),
        "Délelőtt": (10, 13),
        "Délután": (13, 17),
        "Este": (17, 22),
        "Zárás körül": (22, 6),
    }
    return windows.get(time_window, (0, 24))
