"""Integration tests for Flow/event APIs."""

from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta, timezone
from decimal import Decimal
from uuid import uuid4
from zoneinfo import ZoneInfo

from fastapi.testclient import TestClient
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.main import app
from app.modules.events.infrastructure.orm.event_ticket_actual_model import (
    EventTicketActualModel,
)
from app.modules.imports.infrastructure.orm.import_batch_model import ImportBatchModel
from app.modules.imports.infrastructure.orm.import_file_model import ImportFileModel
from app.modules.imports.infrastructure.orm.import_row_model import ImportRowModel
from app.modules.master_data.infrastructure.orm.business_unit_model import (
    BusinessUnitModel,
)
from app.modules.weather.application.commands.sync_shared_weather import (
    SHARED_WEATHER_LATITUDE,
    SHARED_WEATHER_LOCATION_NAME,
    SHARED_WEATHER_LONGITUDE,
    SHARED_WEATHER_PROVIDER,
    SHARED_WEATHER_TIMEZONE,
)
from app.modules.weather.application.services.weather_provider import (
    FetchedWeatherObservation,
)
from app.modules.weather.infrastructure.orm.weather_model import (
    WeatherLocationModel,
    WeatherObservationHourlyModel,
)
from app.modules.weather.presentation.dependencies import get_weather_provider

API_PREFIX = "/api/v1/events"


class FakeWeatherProvider:
    """Deterministic weather provider for event weather coverage tests."""

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
            observations.append(
                FetchedWeatherObservation(
                    observed_at=current.astimezone(timezone.utc),
                    provider=self.provider_name,
                    provider_model="event-coverage-test",
                    weather_code=0,
                    weather_condition="napos",
                    temperature_c=Decimal("24"),
                    apparent_temperature_c=Decimal("25"),
                    relative_humidity_percent=Decimal("55"),
                    precipitation_mm=Decimal("0"),
                    rain_mm=Decimal("0"),
                    snowfall_cm=Decimal("0"),
                    cloud_cover_percent=Decimal("15"),
                    wind_speed_kmh=Decimal("9"),
                    wind_gust_kmh=Decimal("14"),
                    pressure_hpa=Decimal("1010"),
                    source_payload={"event_test": True},
                )
            )
            current += timedelta(hours=1)
        return observations


def _create_event_pos_row(
    db_session: Session,
    *,
    business_unit_id,
    row_number: int,
    occurred_at: datetime,
    receipt_no: str,
    category_name: str,
    product_name: str,
    quantity: Decimal,
    gross_amount: Decimal,
) -> ImportRowModel:
    payload = {
        "date": occurred_at.date().isoformat(),
        "occurred_at": occurred_at.isoformat(),
        "receipt_no": receipt_no,
        "category_name": category_name,
        "product_name": product_name,
        "quantity": str(quantity),
        "gross_amount": str(gross_amount),
        "payment_method": "cash",
    }
    batch = ImportBatchModel(
        business_unit_id=business_unit_id,
        import_type="flow_pos_sales",
        status="parsed",
        started_at=datetime.now(UTC),
        finished_at=datetime.now(UTC),
        total_rows=1,
        parsed_rows=1,
        error_rows=0,
    )
    db_session.add(batch)
    db_session.flush()
    import_file = ImportFileModel(
        batch_id=batch.id,
        original_name=f"event-performance-{row_number}.csv",
        stored_path=f"storage/imports/event-performance-{uuid4().hex}.csv",
        mime_type="text/csv",
        size_bytes=128,
    )
    db_session.add(import_file)
    db_session.flush()
    row = ImportRowModel(
        batch_id=batch.id,
        file_id=import_file.id,
        row_number=row_number,
        raw_payload=payload,
        normalized_payload=payload,
        parse_status="parsed",
    )
    db_session.add(row)
    db_session.commit()
    db_session.refresh(row)
    return row


def test_create_event_succeeds_with_settlement_lite_fields(
    client: TestClient,
    test_business_unit: BusinessUnitModel,
) -> None:
    response = client.post(
        API_PREFIX,
        json={
            "business_unit_id": str(test_business_unit.id),
            "title": "Péntek esti koncert",
            "status": "confirmed",
            "starts_at": datetime(2026, 5, 1, 20, 0, tzinfo=timezone.utc).isoformat(),
            "performer_name": "Teszt Zenekar",
            "expected_attendance": 180,
            "ticket_revenue_gross": "1000000",
            "bar_revenue_gross": "450000",
            "performer_share_percent": "80",
            "performer_fixed_fee": "0",
            "event_cost_amount": "100000",
            "notes": "Első event MVP teszt",
            "is_active": True,
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["title"] == "Péntek esti koncert"
    assert payload["status"] == "confirmed"
    assert payload["performer_share_amount"] == "800000.00"
    assert payload["retained_ticket_revenue"] == "200000.00"
    assert payload["own_revenue"] == "650000.00"
    assert payload["event_profit_lite"] == "550000.00"


def test_list_events_filters_by_business_unit_and_status(
    client: TestClient,
    test_business_unit: BusinessUnitModel,
) -> None:
    client.post(
        API_PREFIX,
        json={
            "business_unit_id": str(test_business_unit.id),
            "title": "Szombati koncert",
            "status": "planned",
            "starts_at": datetime(2026, 5, 2, 20, 0, tzinfo=timezone.utc).isoformat(),
        },
    )
    client.post(
        API_PREFIX,
        json={
            "business_unit_id": str(test_business_unit.id),
            "title": "Lezárt koncert",
            "status": "completed",
            "starts_at": datetime(2026, 4, 25, 20, 0, tzinfo=timezone.utc).isoformat(),
        },
    )

    response = client.get(
        API_PREFIX,
        params={
            "business_unit_id": str(test_business_unit.id),
            "status": "planned",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["title"] == "Szombati koncert"


def test_list_events_filters_by_start_window(
    client: TestClient,
    test_business_unit: BusinessUnitModel,
) -> None:
    client.post(
        API_PREFIX,
        json={
            "business_unit_id": str(test_business_unit.id),
            "title": "Május eleji koncert",
            "status": "completed",
            "starts_at": datetime(2026, 5, 2, 20, 0, tzinfo=timezone.utc).isoformat(),
        },
    )
    client.post(
        API_PREFIX,
        json={
            "business_unit_id": str(test_business_unit.id),
            "title": "Júniusi koncert",
            "status": "completed",
            "starts_at": datetime(2026, 6, 6, 20, 0, tzinfo=timezone.utc).isoformat(),
        },
    )

    response = client.get(
        API_PREFIX,
        params={
            "business_unit_id": str(test_business_unit.id),
            "starts_from": datetime(2026, 5, 1, 0, 0, tzinfo=timezone.utc).isoformat(),
            "starts_to": datetime(2026, 5, 31, 23, 59, tzinfo=timezone.utc).isoformat(),
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert [item["title"] for item in payload] == ["Május eleji koncert"]


def test_event_performance_aggregates_pos_rows_and_weather_context(
    client: TestClient,
    db_session: Session,
    test_business_unit: BusinessUnitModel,
) -> None:
    create_response = client.post(
        API_PREFIX,
        json={
            "business_unit_id": str(test_business_unit.id),
            "title": "Flow performance koncert",
            "status": "confirmed",
            "starts_at": datetime(2026, 6, 16, 18, 0, tzinfo=timezone.utc).isoformat(),
            "ends_at": datetime(2026, 6, 16, 23, 0, tzinfo=timezone.utc).isoformat(),
            "performer_share_percent": "80",
            "performer_fixed_fee": "10000",
            "event_cost_amount": "5000",
        },
    )
    assert create_response.status_code == 201
    event_id = create_response.json()["id"]

    row_ids = [
        _create_event_pos_row(
            db_session,
            business_unit_id=test_business_unit.id,
            row_number=1,
            occurred_at=datetime(2026, 6, 16, 19, 0, tzinfo=timezone.utc),
            receipt_no="EVENT-1",
            category_name="Jegyek",
            product_name="VIP belépő",
            quantity=Decimal("3"),
            gross_amount=Decimal("30000"),
        ).id,
        _create_event_pos_row(
            db_session,
            business_unit_id=test_business_unit.id,
            row_number=2,
            occurred_at=datetime(2026, 6, 16, 20, 0, tzinfo=timezone.utc),
            receipt_no="EVENT-2",
            category_name="Ital",
            product_name="Sör",
            quantity=Decimal("10"),
            gross_amount=Decimal("45000"),
        ).id,
        _create_event_pos_row(
            db_session,
            business_unit_id=test_business_unit.id,
            row_number=3,
            occurred_at=datetime(2026, 6, 16, 21, 0, tzinfo=timezone.utc),
            receipt_no="EVENT-2",
            category_name="Ital",
            product_name="Koktél",
            quantity=Decimal("2"),
            gross_amount=Decimal("15000"),
        ).id,
        _create_event_pos_row(
            db_session,
            business_unit_id=test_business_unit.id,
            row_number=4,
            occurred_at=datetime(2026, 6, 17, 10, 0, tzinfo=timezone.utc),
            receipt_no="EVENT-OUTSIDE",
            category_name="Ital",
            product_name="Kávé",
            quantity=Decimal("1"),
            gross_amount=Decimal("9999"),
        ).id,
    ]

    created_location = False
    weather_location = db_session.scalar(
        select(WeatherLocationModel)
        .where(WeatherLocationModel.scope == "shared")
        .where(WeatherLocationModel.name == SHARED_WEATHER_LOCATION_NAME)
        .where(WeatherLocationModel.provider == SHARED_WEATHER_PROVIDER)
    )
    if weather_location is None:
        weather_location = WeatherLocationModel(
            scope="shared",
            name=SHARED_WEATHER_LOCATION_NAME,
            latitude=SHARED_WEATHER_LATITUDE,
            longitude=SHARED_WEATHER_LONGITUDE,
            timezone=SHARED_WEATHER_TIMEZONE,
            provider=SHARED_WEATHER_PROVIDER,
            is_active=True,
        )
        db_session.add(weather_location)
        db_session.commit()
        db_session.refresh(weather_location)
        created_location = True

    observations = [
        WeatherObservationHourlyModel(
            weather_location_id=weather_location.id,
            observed_at=datetime(2026, 6, 16, 19, 0, tzinfo=timezone.utc),
            provider=SHARED_WEATHER_PROVIDER,
            weather_condition="napos",
            temperature_c=Decimal("28"),
            precipitation_mm=Decimal("0"),
            cloud_cover_percent=Decimal("10"),
            wind_speed_kmh=Decimal("8"),
        ),
        WeatherObservationHourlyModel(
            weather_location_id=weather_location.id,
            observed_at=datetime(2026, 6, 16, 20, 0, tzinfo=timezone.utc),
            provider=SHARED_WEATHER_PROVIDER,
            weather_condition="napos",
            temperature_c=Decimal("26"),
            precipitation_mm=Decimal("0"),
            cloud_cover_percent=Decimal("20"),
            wind_speed_kmh=Decimal("10"),
        ),
    ]
    db_session.add_all(observations)
    db_session.commit()
    observation_ids = [observation.id for observation in observations]

    try:
        response = client.get(f"{API_PREFIX}/{event_id}/performance")

        assert response.status_code == 200
        payload = response.json()
        assert payload["source_row_count"] == 3
        assert payload["receipt_count"] == 2
        assert payload["ticket_revenue_gross"] == "30000.00"
        assert payload["bar_revenue_gross"] == "60000.00"
        assert payload["total_revenue_gross"] == "90000.00"
        assert payload["performer_share_amount"] == "24000.00"
        assert payload["retained_ticket_revenue"] == "6000.00"
        assert payload["own_revenue"] == "66000.00"
        assert payload["event_profit_lite"] == "51000.00"
        assert payload["weather"]["observation_count"] == 2
        assert payload["weather"]["dominant_condition"] == "napos"
        assert payload["categories"][0]["category_name"] == "Ital"

        list_response = client.get(
            f"{API_PREFIX}/performance",
            params={"business_unit_id": str(test_business_unit.id), "status": "confirmed"},
        )

        assert list_response.status_code == 200
        listed_payload = [
            item for item in list_response.json() if item["event_id"] == event_id
        ][0]
        assert listed_payload["ticket_revenue_gross"] == "30000.00"
        assert listed_payload["bar_revenue_gross"] == "60000.00"
        assert listed_payload["event_profit_lite"] == "51000.00"
    finally:
        db_session.execute(
            delete(WeatherObservationHourlyModel).where(
                WeatherObservationHourlyModel.id.in_(observation_ids)
            )
        )
        if created_location:
            db_session.execute(
                delete(WeatherLocationModel).where(WeatherLocationModel.id == weather_location.id)
            )
        db_session.execute(delete(ImportRowModel).where(ImportRowModel.id.in_(row_ids)))
        db_session.commit()


def test_event_ticket_actual_overrides_ticket_layer_in_performance(
    client: TestClient,
    db_session: Session,
    test_business_unit: BusinessUnitModel,
) -> None:
    create_response = client.post(
        API_PREFIX,
        json={
            "business_unit_id": str(test_business_unit.id),
            "title": "Ticket rendszeres event",
            "status": "completed",
            "starts_at": datetime(2026, 7, 4, 18, 0, tzinfo=timezone.utc).isoformat(),
            "ends_at": datetime(2026, 7, 4, 23, 0, tzinfo=timezone.utc).isoformat(),
            "performer_share_percent": "80",
            "performer_fixed_fee": "10000",
            "event_cost_amount": "5000",
        },
    )
    assert create_response.status_code == 201
    event_id = create_response.json()["id"]

    row = _create_event_pos_row(
        db_session,
        business_unit_id=test_business_unit.id,
        row_number=101,
        occurred_at=datetime(2026, 7, 4, 20, 0, tzinfo=timezone.utc),
        receipt_no="TICKET-ACTUAL-BAR",
        category_name="Ital",
        product_name="Fröccs",
        quantity=Decimal("8"),
        gross_amount=Decimal("24000"),
    )

    try:
        upsert_response = client.put(
            f"{API_PREFIX}/{event_id}/ticket-actual",
            json={
                "source_name": "Ticket platform",
                "source_reference": "settlement-2026-07-04",
                "sold_quantity": "120",
                "gross_revenue": "600000",
                "platform_fee_gross": "30000",
                "notes": "Manual test settlement",
            },
        )
        assert upsert_response.status_code == 200
        actual_payload = upsert_response.json()
        assert actual_payload["sold_quantity"] == "120.000"
        assert actual_payload["gross_revenue"] == "600000.00"

        get_response = client.get(f"{API_PREFIX}/{event_id}/ticket-actual")
        assert get_response.status_code == 200
        assert get_response.json()["source_name"] == "Ticket platform"

        performance_response = client.get(f"{API_PREFIX}/{event_id}/performance")
        assert performance_response.status_code == 200
        payload = performance_response.json()
        assert payload["ticket_revenue_gross"] == "600000.00"
        assert payload["ticket_quantity"] == "120.000"
        assert payload["bar_revenue_gross"] == "24000.00"
        assert payload["performer_share_amount"] == "480000.00"
        assert payload["event_profit_lite"] == "129000.00"
    finally:
        db_session.execute(
            delete(EventTicketActualModel).where(
                EventTicketActualModel.event_id == event_id
            )
        )
        db_session.execute(delete(ImportRowModel).where(ImportRowModel.id == row.id))
        db_session.commit()


def test_event_weather_coverage_backfills_shared_interval_idempotently(
    client: TestClient,
    db_session: Session,
    test_business_unit: BusinessUnitModel,
) -> None:
    create_response = client.post(
        API_PREFIX,
        json={
            "business_unit_id": str(test_business_unit.id),
            "title": "Historikus weather event",
            "status": "confirmed",
            "starts_at": datetime(2026, 4, 12, 20, 0, tzinfo=timezone.utc).isoformat(),
            "ends_at": datetime(2026, 4, 13, 2, 0, tzinfo=timezone.utc).isoformat(),
            "performer_name": "Weather Teszt",
            "performer_share_percent": "80",
        },
    )
    assert create_response.status_code == 201
    event_id = create_response.json()["id"]
    provider = FakeWeatherProvider()
    app.dependency_overrides[get_weather_provider] = lambda: provider
    try:
        first_response = client.post(f"{API_PREFIX}/{event_id}/weather/ensure-coverage")
        assert first_response.status_code == 201
        first_payload = first_response.json()
        assert first_payload["status"] in {"backfilled", "covered"}
        assert first_payload["requested_hours"] > 0
        assert first_payload["missing_hours"] == 0

        performance_response = client.get(f"{API_PREFIX}/{event_id}/performance")
        assert performance_response.status_code == 200
        assert performance_response.json()["weather"]["observation_count"] > 0

        second_response = client.post(f"{API_PREFIX}/{event_id}/weather/ensure-coverage")
        assert second_response.status_code == 201
        second_payload = second_response.json()
        assert second_payload["status"] == "covered"
        assert second_payload["backfill_attempted"] is False
        assert provider.calls <= 1
    finally:
        app.dependency_overrides.clear()
        _delete_event_coverage_weather_test_data(db_session)


def test_create_event_rejects_invalid_performer_share(
    client: TestClient,
    test_business_unit: BusinessUnitModel,
) -> None:
    response = client.post(
        API_PREFIX,
        json={
            "business_unit_id": str(test_business_unit.id),
            "title": "Hibás share",
            "status": "planned",
            "starts_at": datetime(2026, 5, 3, 20, 0, tzinfo=timezone.utc).isoformat(),
            "performer_share_percent": "120",
        },
    )

    assert response.status_code == 422


def test_create_event_with_invalid_business_unit_returns_not_found(
    client: TestClient,
) -> None:
    response = client.post(
        API_PREFIX,
        json={
            "business_unit_id": str(uuid4()),
            "title": "Ghost event",
            "status": "planned",
            "starts_at": datetime(2026, 5, 3, 20, 0, tzinfo=timezone.utc).isoformat(),
        },
    )

    assert response.status_code == 404
    assert "Business unit" in response.json()["detail"]


def test_update_and_archive_event(
    client: TestClient,
    test_business_unit: BusinessUnitModel,
) -> None:
    create_response = client.post(
        API_PREFIX,
        json={
            "business_unit_id": str(test_business_unit.id),
            "title": "Módosítandó koncert",
            "status": "planned",
            "starts_at": datetime(2026, 5, 4, 20, 0, tzinfo=timezone.utc).isoformat(),
        },
    )
    event_id = create_response.json()["id"]

    update_response = client.put(
        f"{API_PREFIX}/{event_id}",
        json={
            "business_unit_id": str(test_business_unit.id),
            "title": "Módosított koncert",
            "status": "completed",
            "starts_at": datetime(2026, 5, 4, 20, 0, tzinfo=timezone.utc).isoformat(),
            "ticket_revenue_gross": "500000",
            "bar_revenue_gross": "300000",
            "performer_share_percent": "70",
            "performer_fixed_fee": "50000",
            "event_cost_amount": "25000",
        },
    )

    assert update_response.status_code == 200
    assert update_response.json()["title"] == "Módosított koncert"
    assert update_response.json()["event_profit_lite"] == "375000.00"

    archive_response = client.delete(f"{API_PREFIX}/{event_id}")

    assert archive_response.status_code == 200
    assert archive_response.json()["is_active"] is False


def _delete_event_coverage_weather_test_data(db_session: Session) -> None:
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
    if not location_ids:
        return

    db_session.execute(
        delete(WeatherObservationHourlyModel).where(
            WeatherObservationHourlyModel.weather_location_id.in_(location_ids)
        ).where(
            WeatherObservationHourlyModel.provider_model == "event-coverage-test"
        )
    )
    db_session.commit()
