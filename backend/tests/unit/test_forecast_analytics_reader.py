"""Unit tests for shared forecast cache aggregation rules."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace
from zoneinfo import ZoneInfo

from app.modules.analytics.infrastructure.repositories.forecast_analytics_reader import (
    ForecastAnalyticsReader,
    forecast_condition_band,
    forecast_precipitation,
    time_window_hours,
    time_window_label,
)

TIME_ZONE = ZoneInfo("Europe/Budapest")


class _SessionStub:
    pass


def _forecast(
    *,
    forecasted_at: datetime,
    temperature: str = "25",
    cloud_cover: str = "10",
    precipitation: str = "0",
    forecast_run_at: datetime | None = None,
) -> SimpleNamespace:
    return SimpleNamespace(
        forecasted_at=forecasted_at,
        temperature_c=Decimal(temperature),
        cloud_cover_percent=Decimal(cloud_cover),
        precipitation_mm=Decimal(precipitation),
        rain_mm=Decimal("0"),
        snowfall_cm=Decimal("0"),
        forecast_run_at=forecast_run_at,
    )


def _reader() -> ForecastAnalyticsReader:
    return ForecastAnalyticsReader(
        _SessionStub(),
        time_zone=TIME_ZONE,
        location_name="Szolnok",
        provider="open_meteo",
    )


def test_daily_aggregation_sums_weather_and_keeps_latest_run() -> None:
    first_run = datetime(2026, 6, 20, 6, tzinfo=UTC)
    latest_run = datetime(2026, 6, 20, 7, tzinfo=UTC)
    result = _reader().aggregate_days(
        [
            _forecast(
                forecasted_at=datetime(2026, 6, 22, 8, tzinfo=UTC),
                precipitation="1.5",
                forecast_run_at=first_run,
            ),
            _forecast(
                forecasted_at=datetime(2026, 6, 22, 9, tzinfo=UTC),
                temperature="27",
                forecast_run_at=latest_run,
            ),
        ]
    )

    values = result[datetime(2026, 6, 22, tzinfo=TIME_ZONE).date()]
    assert values["hour_count"] == 2
    assert values["temperatures"] == [Decimal("25"), Decimal("27")]
    assert values["precipitation_sum"] == Decimal("1.5")
    assert values["condition_counts"]["csapadekos"] == 1
    assert values["condition_counts"]["napos_szaraz"] == 1
    assert values["latest_forecast_run_at"] == latest_run


def test_time_window_aggregation_uses_local_business_time() -> None:
    result = _reader().aggregate_time_windows(
        [
            _forecast(
                forecasted_at=datetime(2026, 6, 22, 12, tzinfo=UTC),
            )
        ]
    )

    key = (datetime(2026, 6, 22, tzinfo=TIME_ZONE).date(), "Délután")
    assert key in result
    assert result[key]["temperatures"] == [Decimal("25")]


def test_event_window_includes_every_available_hour_until_end() -> None:
    starts_at = datetime(2026, 6, 22, 18, 15, tzinfo=TIME_ZONE)
    ends_at = datetime(2026, 6, 22, 20, 10, tzinfo=TIME_ZONE)
    rows = [
        _forecast(forecasted_at=datetime(2026, 6, 22, hour, tzinfo=UTC))
        for hour in (16, 17, 18)
    ]
    by_hour = {row.forecasted_at: row for row in rows}

    result = _reader().event_window(
        starts_at=starts_at,
        ends_at=ends_at,
        forecasts_by_hour=by_hour,
    )

    assert result == rows


def test_forecast_classification_and_time_window_boundaries() -> None:
    rainy = _forecast(
        forecasted_at=datetime(2026, 6, 22, tzinfo=UTC),
        cloud_cover="0",
        precipitation="0.5",
    )
    assert forecast_precipitation(rainy) == Decimal("0.5")
    assert forecast_condition_band(rainy) == "csapadekos"
    assert time_window_label(6) == "Reggel"
    assert time_window_label(13) == "Délután"
    assert time_window_label(22) == "Zárás körül"
    assert time_window_hours("Este") == (17, 22)
