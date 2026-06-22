"""Unit tests for historical weather-enriched analytics."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from types import SimpleNamespace
from zoneinfo import ZoneInfo

from app.modules.analytics.infrastructure.repositories.weather_analytics_reader import (
    WeatherAnalyticsReader,
    observation_precipitation,
    temperature_band,
    weather_condition_band,
)

TIME_ZONE = ZoneInfo("Europe/Budapest")
START_AT = datetime(2026, 6, 1, tzinfo=TIME_ZONE)
END_AT = datetime(2026, 6, 30, 23, 59, 59, tzinfo=TIME_ZONE)


class _ScalarResult:
    def __init__(self, rows: list[SimpleNamespace]) -> None:
        self._rows = rows

    def all(self) -> list[SimpleNamespace]:
        return self._rows


class _SessionStub:
    def __init__(self, observations: list[SimpleNamespace]) -> None:
        self._observations = observations

    def scalars(self, _statement: object) -> _ScalarResult:
        return _ScalarResult(self._observations)


def _observation(
    *,
    temperature: str = "26",
    condition: str = "napos",
    cloud_cover: str = "10",
    precipitation: str = "0",
) -> SimpleNamespace:
    return SimpleNamespace(
        observed_at=datetime(2026, 6, 10, 8, tzinfo=ZoneInfo("UTC")),
        weather_condition=condition,
        temperature_c=Decimal(temperature),
        cloud_cover_percent=Decimal(cloud_cover),
        precipitation_mm=Decimal(precipitation),
        rain_mm=Decimal("0"),
        snowfall_cm=Decimal("0"),
    )


def _row(
    *,
    row_number: int,
    receipt_no: str,
    category_name: str,
    gross_amount: str,
    quantity: str = "1",
) -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid.uuid4(),
        row_number=row_number,
        normalized_payload={
            "occurred_at": "2026-06-10T10:15:00+02:00",
            "date": "2026-06-10",
            "receipt_no": receipt_no,
            "category_name": category_name,
            "gross_amount": gross_amount,
            "quantity": quantity,
        },
    )


def _reader(observations: list[SimpleNamespace]) -> WeatherAnalyticsReader:
    return WeatherAnalyticsReader(
        _SessionStub(observations),
        time_zone=TIME_ZONE,
        location_name="Szolnok",
        provider="open_meteo",
        unknown_category="Kategória nélkül",
    )


def test_category_insights_join_pos_rows_to_hourly_weather() -> None:
    result = _reader([_observation()]).build_category_insights(
        rows=[
            _row(
                row_number=1,
                receipt_no="R-1",
                category_name="Fagyi",
                gross_amount="1800",
                quantity="2",
            )
        ],
        start_at=START_AT,
        end_at=END_AT,
        limit=10,
    )

    assert len(result) == 1
    assert result[0].category_name == "Fagyi"
    assert result[0].revenue == Decimal("1800")
    assert result[0].quantity == Decimal("2")
    assert result[0].average_temperature_c == Decimal("26")


def test_temperature_band_insights_group_receipts_and_rank_category() -> None:
    result = _reader([_observation()]).build_temperature_band_insights(
        rows=[
            _row(
                row_number=1,
                receipt_no="R-1",
                category_name="Fagyi",
                gross_amount="1800",
            ),
            _row(
                row_number=2,
                receipt_no="R-1",
                category_name="Kávé",
                gross_amount="700",
            ),
        ],
        start_at=START_AT,
        end_at=END_AT,
    )

    assert len(result) == 1
    assert result[0].temperature_band == "meleg"
    assert result[0].basket_count == 1
    assert result[0].average_basket_value == Decimal("2500")
    assert result[0].top_category_name == "Fagyi"


def test_condition_insights_prioritize_precipitation_over_cloud_cover() -> None:
    observation = _observation(cloud_cover="90", precipitation="1.5")
    result = _reader([observation]).build_condition_insights(
        rows=[
            _row(
                row_number=1,
                receipt_no="R-1",
                category_name="Tea",
                gross_amount="1200",
            )
        ],
        start_at=START_AT,
        end_at=END_AT,
    )

    assert len(result) == 1
    assert result[0].condition_band == "csapadekos"
    assert result[0].precipitation_mm == Decimal("1.5")
    assert result[0].average_cloud_cover_percent == Decimal("90")


def test_weather_classification_helpers_keep_boundary_rules_explicit() -> None:
    assert temperature_band(Decimal("9.99")) == "hideg"
    assert temperature_band(Decimal("10")) == "enyhe"
    assert temperature_band(Decimal("20")) == "meleg"
    assert temperature_band(Decimal("28")) == "kanikula"

    rainy = _observation(cloud_cover="0", precipitation="0.5")
    cloudy = _observation(cloud_cover="70")
    partial = _observation(cloud_cover="35")
    sunny = _observation(cloud_cover="34")
    assert weather_condition_band(rainy) == "csapadekos"
    assert weather_condition_band(cloudy) == "borult"
    assert weather_condition_band(partial) == "reszben_felhos"
    assert weather_condition_band(sunny) == "napos_szaraz"
    assert observation_precipitation(rainy) == Decimal("0.5")
