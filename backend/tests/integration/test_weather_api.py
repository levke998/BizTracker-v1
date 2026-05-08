"""Integration tests for weather cache APIs."""

from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from zoneinfo import ZoneInfo

from fastapi.testclient import TestClient
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.main import app
from app.modules.master_data.infrastructure.orm.business_unit_model import (
    BusinessUnitModel,
)
from app.modules.weather.application.services.weather_provider import (
    FetchedWeatherForecast,
    FetchedWeatherObservation,
)
from app.modules.weather.application.commands.sync_shared_weather import (
    SHARED_WEATHER_LOCATION_NAME,
)
from app.modules.weather.infrastructure.orm.weather_model import (
    WeatherForecastHourlyModel,
    WeatherLocationModel,
    WeatherObservationHourlyModel,
)
from app.modules.weather.presentation.dependencies import get_weather_provider

API_PREFIX = "/api/v1/weather"
IMPORTS_API_PREFIX = "/api/v1/imports"


class FakeWeatherProvider:
    """Deterministic weather provider for integration tests."""

    provider_name = "open_meteo"

    def __init__(self) -> None:
        self.calls = 0

    def fetch_hourly(
        self,
        *,
        latitude: Decimal,
        longitude: Decimal,
        timezone_name: str,
        start_date: date,
        end_date: date,
    ) -> list[FetchedWeatherObservation]:
        self.calls += 1
        zone = ZoneInfo(timezone_name)
        current = datetime.combine(start_date, time.min, tzinfo=zone)
        end = datetime.combine(end_date, time(hour=23), tzinfo=zone)
        observations: list[FetchedWeatherObservation] = []
        while current <= end:
            observed_at = current.astimezone(timezone.utc)
            observations.append(
                FetchedWeatherObservation(
                    observed_at=observed_at,
                    provider=self.provider_name,
                    provider_model="fake-model",
                    weather_code=0 if current.hour < 12 else 61,
                    weather_condition="napos" if current.hour < 12 else "esos",
                    temperature_c=Decimal("24.5"),
                    apparent_temperature_c=Decimal("25.0"),
                    relative_humidity_percent=Decimal("55"),
                    precipitation_mm=Decimal("0") if current.hour < 12 else Decimal("1.2"),
                    rain_mm=Decimal("0") if current.hour < 12 else Decimal("1.2"),
                    snowfall_cm=Decimal("0"),
                    cloud_cover_percent=Decimal("20"),
                    wind_speed_kmh=Decimal("12"),
                    wind_gust_kmh=Decimal("18"),
                    pressure_hpa=Decimal("1012"),
                    source_payload={"fake": True},
                )
            )
            current += timedelta(hours=1)
        return observations

    def fetch_hourly_forecast(
        self,
        *,
        latitude: Decimal,
        longitude: Decimal,
        timezone_name: str,
        forecast_days: int,
    ) -> list[FetchedWeatherForecast]:
        self.calls += 1
        zone = ZoneInfo(timezone_name)
        current = datetime(2036, 5, 1, 0, 0, tzinfo=zone)
        end = current + timedelta(days=forecast_days) - timedelta(hours=1)
        forecasts: list[FetchedWeatherForecast] = []
        run_at = datetime(2036, 4, 30, 12, 0, tzinfo=timezone.utc)
        while current <= end:
            forecasted_at = current.astimezone(timezone.utc)
            forecasts.append(
                FetchedWeatherForecast(
                    forecasted_at=forecasted_at,
                    provider=self.provider_name,
                    provider_model="fake-forecast-model",
                    forecast_run_at=run_at,
                    weather_code=0,
                    weather_condition="napos",
                    temperature_c=Decimal("26.0"),
                    apparent_temperature_c=Decimal("27.0"),
                    relative_humidity_percent=Decimal("52"),
                    precipitation_mm=Decimal("0"),
                    rain_mm=Decimal("0"),
                    snowfall_cm=Decimal("0"),
                    cloud_cover_percent=Decimal("18"),
                    wind_speed_kmh=Decimal("10"),
                    wind_gust_kmh=Decimal("16"),
                    pressure_hpa=Decimal("1011"),
                    source_payload={"fake_forecast": True},
                )
            )
            current += timedelta(hours=1)
        return forecasts


def test_weather_backfill_creates_location_and_observations(
    client: TestClient,
    test_business_unit: BusinessUnitModel,
) -> None:
    provider = FakeWeatherProvider()
    app.dependency_overrides[get_weather_provider] = lambda: provider
    try:
        response = client.post(
            f"{API_PREFIX}/backfill",
            json={
                "business_unit_id": str(test_business_unit.id),
                "name": "Gourmand belvaros",
                "latitude": "47.497913",
                "longitude": "19.040236",
                "start_date": "2026-04-12",
                "end_date": "2026-04-12",
                "timezone_name": "Europe/Budapest",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    payload = response.json()
    assert payload["requested_hours"] == 24
    assert payload["created_count"] == 24
    assert payload["updated_count"] == 0
    assert payload["skipped_count"] == 0
    assert provider.calls == 1

    observations_response = client.get(
        f"{API_PREFIX}/observations",
        params={
            "business_unit_id": str(test_business_unit.id),
            "limit": 50,
        },
    )
    assert observations_response.status_code == 200
    observations = observations_response.json()
    assert len(observations) == 24
    assert {item["weather_condition"] for item in observations} == {"napos", "esos"}


def test_weather_backfill_skips_fully_cached_range(
    client: TestClient,
    test_business_unit: BusinessUnitModel,
) -> None:
    provider = FakeWeatherProvider()
    app.dependency_overrides[get_weather_provider] = lambda: provider
    try:
        payload = {
            "business_unit_id": str(test_business_unit.id),
            "name": "Flow kert",
            "latitude": "47.497913",
            "longitude": "19.040236",
            "start_date": "2026-04-13",
            "end_date": "2026-04-13",
            "timezone_name": "Europe/Budapest",
        }
        first_response = client.post(f"{API_PREFIX}/backfill", json=payload)
        second_response = client.post(f"{API_PREFIX}/backfill", json=payload)
    finally:
        app.dependency_overrides.clear()

    assert first_response.status_code == 201
    assert second_response.status_code == 201
    second_payload = second_response.json()
    assert second_payload["created_count"] == 0
    assert second_payload["updated_count"] == 0
    assert second_payload["skipped_count"] == 24
    assert provider.calls == 1


def test_weather_backfill_rejects_invalid_date_range(
    client: TestClient,
    test_business_unit: BusinessUnitModel,
) -> None:
    response = client.post(
        f"{API_PREFIX}/backfill",
        json={
            "business_unit_id": str(test_business_unit.id),
            "name": "Hibas idoszak",
            "latitude": "47.497913",
            "longitude": "19.040236",
            "start_date": "2026-04-14",
            "end_date": "2026-04-13",
        },
    )

    assert response.status_code == 422


def test_import_batch_weather_recommendation_uses_parsed_pos_time_range(
    client: TestClient,
    test_business_unit: BusinessUnitModel,
    imports_fixtures_dir,
) -> None:
    batch_id = _upload_and_parse_gourmand_package(
        client=client,
        business_unit_id=str(test_business_unit.id),
        imports_fixtures_dir=imports_fixtures_dir,
    )

    response = client.get(f"{API_PREFIX}/import-batches/{batch_id}/recommendation")

    assert response.status_code == 200
    payload = response.json()
    assert payload["can_backfill"] is True
    assert payload["start_date"] == "2026-04-12"
    assert payload["end_date"] == "2026-04-20"
    assert payload["requested_hours"] == 216
    assert payload["cached_hours"] >= 0
    assert payload["missing_hours"] == max(
        payload["requested_hours"] - payload["cached_hours"],
        0,
    )
    assert payload["suggested_location_name"] == SHARED_WEATHER_LOCATION_NAME


def test_import_batch_weather_backfill_caches_and_updates_recommendation(
    client: TestClient,
    db_session: Session,
    test_business_unit: BusinessUnitModel,
    imports_fixtures_dir,
) -> None:
    batch_id = _upload_and_parse_gourmand_package(
        client=client,
        business_unit_id=str(test_business_unit.id),
        imports_fixtures_dir=imports_fixtures_dir,
    )
    provider = FakeWeatherProvider()
    app.dependency_overrides[get_weather_provider] = lambda: provider
    try:
        initial_recommendation_response = client.get(
            f"{API_PREFIX}/import-batches/{batch_id}/recommendation"
        )
        assert initial_recommendation_response.status_code == 200
        expected_created = initial_recommendation_response.json()["missing_hours"]

        backfill_response = client.post(f"{API_PREFIX}/import-batches/{batch_id}/backfill")
        assert backfill_response.status_code == 201
        backfill_payload = backfill_response.json()
        assert backfill_payload["created_count"] == expected_created
        assert backfill_payload["skipped_count"] == 216 - expected_created
        assert provider.calls == (1 if expected_created > 0 else 0)

        recommendation_response = client.get(
            f"{API_PREFIX}/import-batches/{batch_id}/recommendation"
        )
        assert recommendation_response.status_code == 200
        recommendation = recommendation_response.json()
        assert recommendation["cached_hours"] >= 216
        assert recommendation["missing_hours"] == 0
    finally:
        app.dependency_overrides.clear()
        _delete_shared_weather_test_data(db_session)


def test_import_batch_weather_ensure_coverage_is_idempotent(
    client: TestClient,
    db_session: Session,
    test_business_unit: BusinessUnitModel,
    imports_fixtures_dir,
) -> None:
    batch_id = _upload_and_parse_gourmand_package(
        client=client,
        business_unit_id=str(test_business_unit.id),
        imports_fixtures_dir=imports_fixtures_dir,
    )
    provider = FakeWeatherProvider()
    app.dependency_overrides[get_weather_provider] = lambda: provider
    try:
        first_response = client.post(
            f"{API_PREFIX}/import-batches/{batch_id}/ensure-coverage"
        )
        assert first_response.status_code == 201
        first_payload = first_response.json()
        assert first_payload["status"] in {"backfilled", "covered"}
        assert first_payload["missing_hours"] == 0
        assert first_payload["requested_hours"] == 216

        second_response = client.post(
            f"{API_PREFIX}/import-batches/{batch_id}/ensure-coverage"
        )
        assert second_response.status_code == 201
        second_payload = second_response.json()
        assert second_payload["status"] == "covered"
        assert second_payload["backfill_attempted"] is False
        assert second_payload["missing_hours"] == 0
        assert provider.calls <= 1
    finally:
        app.dependency_overrides.clear()
        _delete_shared_weather_test_data(db_session)


def test_shared_szolnok_weather_sync_uses_common_location(
    client: TestClient,
    db_session: Session,
) -> None:
    provider = FakeWeatherProvider()
    app.dependency_overrides[get_weather_provider] = lambda: provider
    try:
        response = client.post(f"{API_PREFIX}/sync/szolnok", params={"days_back": 0})
    finally:
        app.dependency_overrides.clear()
        _delete_shared_weather_test_data(db_session)

    assert response.status_code == 201
    payload = response.json()
    assert payload["weather_location"]["name"] == SHARED_WEATHER_LOCATION_NAME
    assert payload["weather_location"]["scope"] == "shared"
    assert payload["weather_location"]["business_unit_id"] is None
    assert payload["requested_hours"] == 24
    assert (
        payload["created_count"] + payload["updated_count"] + payload["skipped_count"]
        == 24
    )
    assert provider.calls <= 1


def test_shared_szolnok_weather_forecast_sync_is_upserted(
    client: TestClient,
    db_session: Session,
) -> None:
    provider = FakeWeatherProvider()
    app.dependency_overrides[get_weather_provider] = lambda: provider
    try:
        first_response = client.post(
            f"{API_PREFIX}/forecast/szolnok/sync",
            params={"forecast_days": 2},
        )
        second_response = client.post(
            f"{API_PREFIX}/forecast/szolnok/sync",
            params={"forecast_days": 2},
        )
        forecasts_response = client.get(
            f"{API_PREFIX}/forecasts",
            params={
                "start_at": "2036-05-01T00:00:00+02:00",
                "end_at": "2036-05-03T00:00:00+02:00",
                "limit": 100,
            },
        )
    finally:
        app.dependency_overrides.clear()
        _delete_shared_weather_test_data(db_session)

    assert first_response.status_code == 201
    first_payload = first_response.json()
    assert first_payload["weather_location"]["name"] == SHARED_WEATHER_LOCATION_NAME
    assert first_payload["requested_hours"] == 48
    assert first_payload["created_count"] == 48
    assert first_payload["updated_count"] == 0

    assert second_response.status_code == 201
    second_payload = second_response.json()
    assert second_payload["created_count"] == 0
    assert second_payload["updated_count"] == 48
    assert provider.calls == 2

    assert forecasts_response.status_code == 200
    forecasts = [
        item
        for item in forecasts_response.json()
        if item["provider_model"] == "fake-forecast-model"
    ]
    assert len(forecasts) >= 48
    assert forecasts[0]["weather_condition"] == "napos"


def _upload_and_parse_gourmand_package(
    *,
    client: TestClient,
    business_unit_id: str,
    imports_fixtures_dir,
) -> str:
    files = []
    file_objects = []
    for fixture_name in (
        "gourmand_summary_0412_0427.csv",
        "gourmand_detail_0412_0419.csv",
        "gourmand_detail_0420_0427.csv",
    ):
        file_path = imports_fixtures_dir / fixture_name
        file_object = file_path.open("rb")
        file_objects.append(file_object)
        files.append(("files", (file_path.name, file_object, "text/csv")))

    try:
        upload_response = client.post(
            f"{IMPORTS_API_PREFIX}/file-set",
            data={
                "business_unit_id": business_unit_id,
                "import_type": "gourmand_pos_sales",
            },
            files=files,
        )
    finally:
        for file_object in file_objects:
            file_object.close()

    assert upload_response.status_code == 201
    batch_id = upload_response.json()["id"]
    parse_response = client.post(f"{IMPORTS_API_PREFIX}/batches/{batch_id}/parse")
    assert parse_response.status_code == 200
    return str(batch_id)


def _delete_shared_weather_test_data(db_session: Session) -> None:
    db_session.rollback()
    location_ids = [
        location_id
        for location_id, in db_session.execute(
            select(WeatherLocationModel.id).where(
                WeatherLocationModel.name == SHARED_WEATHER_LOCATION_NAME,
                WeatherLocationModel.scope == "shared",
            )
        ).all()
    ]
    if location_ids:
        db_session.execute(
            delete(WeatherForecastHourlyModel).where(
                WeatherForecastHourlyModel.weather_location_id.in_(location_ids)
            ).where(
                WeatherForecastHourlyModel.provider_model.in_(
                    ["fake-forecast-model"]
                )
            )
        )
        db_session.execute(
            delete(WeatherObservationHourlyModel).where(
                WeatherObservationHourlyModel.weather_location_id.in_(location_ids)
            ).where(
                WeatherObservationHourlyModel.provider_model.in_(
                    ["fake-model", "analytics-test"]
                )
            )
        )
        empty_location_ids = [
            location_id
            for location_id in location_ids
            if not db_session.scalar(
                select(WeatherObservationHourlyModel.id)
                .where(WeatherObservationHourlyModel.weather_location_id == location_id)
                .limit(1)
            )
        ]
        if empty_location_ids:
            db_session.execute(
                delete(WeatherLocationModel).where(
                    WeatherLocationModel.id.in_(empty_location_ids)
                )
            )
        db_session.commit()
