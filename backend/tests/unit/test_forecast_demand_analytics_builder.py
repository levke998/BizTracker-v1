"""Unit tests for forecast demand read-model orchestration."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace
from zoneinfo import ZoneInfo

from app.modules.analytics.infrastructure.repositories.forecast_analytics_reader import (
    ForecastAnalyticsReader,
)
from app.modules.analytics.infrastructure.repositories.forecast_demand_analytics_builder import (
    ForecastDemandAnalyticsBuilder,
)

TIME_ZONE = ZoneInfo("Europe/Budapest")


class _ForecastReaderStub:
    def __init__(self, forecasts: list[SimpleNamespace]) -> None:
        self._forecasts = forecasts
        self._aggregator = ForecastAnalyticsReader(
            SimpleNamespace(),
            time_zone=TIME_ZONE,
            location_name="Szolnok",
            provider="open_meteo",
        )

    def list_forecasts(self, **_kwargs) -> list[SimpleNamespace]:
        return self._forecasts

    def aggregate_days(self, forecasts):
        return self._aggregator.aggregate_days(forecasts)

    def aggregate_time_windows(self, forecasts):
        return self._aggregator.aggregate_time_windows(forecasts)


class _WeatherReaderStub:
    def __init__(self, observations: list[SimpleNamespace]) -> None:
        self._observations = observations

    def list_observations(self, **_kwargs) -> list[SimpleNamespace]:
        return self._observations


def _builder() -> ForecastDemandAnalyticsBuilder:
    historical_at = datetime(2020, 6, 10, 10, tzinfo=TIME_ZONE)
    forecast_at = datetime.now(TIME_ZONE) + timedelta(days=2)
    observation = SimpleNamespace(
        observed_at=historical_at.replace(minute=0),
        temperature_c=Decimal("30"),
        cloud_cover_percent=Decimal("10"),
        precipitation_mm=Decimal("0"),
        rain_mm=Decimal("0"),
        snowfall_cm=Decimal("0"),
    )
    forecast = SimpleNamespace(
        forecasted_at=forecast_at,
        forecast_run_at=datetime.now(TIME_ZONE),
        temperature_c=Decimal("31"),
        cloud_cover_percent=Decimal("10"),
        precipitation_mm=Decimal("0"),
        rain_mm=Decimal("0"),
        snowfall_cm=Decimal("0"),
    )
    return ForecastDemandAnalyticsBuilder(
        forecast_reader=_ForecastReaderStub([forecast]),
        weather_reader=_WeatherReaderStub([observation]),
        time_zone=TIME_ZONE,
        unknown_category="Kategória nélkül",
        unknown_product="Ismeretlen termék",
        horizon_days=7,
    )


def _historical_row() -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid.uuid4(),
        normalized_payload={
            "occurred_at": "2020-06-10T10:15:00+02:00",
            "date": "2020-06-10",
            "receipt_no": "R-1",
            "category_name": "Fagyi",
            "product_name": "Citrom fagyi",
            "gross_amount": "5000",
            "quantity": "5",
        },
    )


def test_impact_uses_matching_historical_weather_baseline() -> None:
    result = _builder().build_impact(rows=[_historical_row()], scope="gourmand")

    assert len(result) == 1
    assert result[0].expected_revenue == Decimal("5000")
    assert result[0].confidence == "magas"
    assert result[0].dominant_temperature_band == "kanikula"


def test_category_and_product_models_share_the_same_historical_truth() -> None:
    builder = _builder()

    categories = builder.build_category_demand(
        rows=[_historical_row()],
        scope="gourmand",
    )
    products = builder.build_product_demand(
        rows=[_historical_row()],
        scope="gourmand",
    )

    assert categories[0].category_name == "Fagyi"
    assert categories[0].expected_quantity == Decimal("5")
    assert products[0].product_name == "Citrom fagyi"
    assert products[0].category_name == "Fagyi"
