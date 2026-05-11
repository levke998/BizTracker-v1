"""Integration tests for the business dashboard read APIs."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from uuid import uuid4
from zoneinfo import ZoneInfo

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.modules.finance.infrastructure.orm.transaction_model import (
    FinancialTransactionModel,
)
from app.modules.events.infrastructure.orm.event_model import EventModel
from app.modules.imports.infrastructure.orm.import_batch_model import ImportBatchModel
from app.modules.imports.infrastructure.orm.import_file_model import ImportFileModel
from app.modules.imports.infrastructure.orm.import_row_model import ImportRowModel
from app.modules.inventory.infrastructure.orm.inventory_item_model import (
    InventoryItemModel,
)
from app.modules.inventory.infrastructure.orm.inventory_movement_model import (
    InventoryMovementModel,
)
from app.modules.master_data.infrastructure.orm.business_unit_model import (
    BusinessUnitModel,
)
from app.modules.master_data.infrastructure.orm.category_model import CategoryModel
from app.modules.master_data.infrastructure.orm.product_model import ProductModel
from app.modules.master_data.infrastructure.orm.unit_of_measure_model import (
    UnitOfMeasureModel,
)
from app.modules.master_data.infrastructure.orm.vat_rate_model import VatRateModel
from app.modules.production.infrastructure.orm.recipe_model import (
    RecipeIngredientModel,
    RecipeModel,
    RecipeVersionModel,
)
from app.modules.weather.application.commands.sync_shared_weather import (
    SHARED_WEATHER_LATITUDE,
    SHARED_WEATHER_LOCATION_NAME,
    SHARED_WEATHER_LONGITUDE,
    SHARED_WEATHER_PROVIDER,
    SHARED_WEATHER_TIMEZONE,
)
from app.modules.weather.infrastructure.orm.weather_model import (
    WeatherForecastHourlyModel,
    WeatherLocationModel,
    WeatherObservationHourlyModel,
)

API_PREFIX = "/api/v1/analytics"
APP_TIME_ZONE = ZoneInfo("Europe/Budapest")


@dataclass
class AnalyticsTestDataBuilder:
    """Create dashboard source records and clean only those records afterwards."""

    db_session: Session
    transaction_ids: list = field(default_factory=list)
    batch_ids: list = field(default_factory=list)
    file_ids: list = field(default_factory=list)
    row_ids: list = field(default_factory=list)
    event_ids: list = field(default_factory=list)
    category_ids: list = field(default_factory=list)
    product_ids: list = field(default_factory=list)
    inventory_item_ids: list = field(default_factory=list)
    movement_ids: list = field(default_factory=list)
    recipe_ids: list = field(default_factory=list)
    recipe_version_ids: list = field(default_factory=list)
    recipe_ingredient_ids: list = field(default_factory=list)
    weather_location_ids: list = field(default_factory=list)
    weather_observation_ids: list = field(default_factory=list)
    weather_forecast_ids: list = field(default_factory=list)

    def create_transaction(
        self,
        *,
        business_unit_id,
        direction: str,
        transaction_type: str,
        amount: Decimal,
        occurred_at: datetime,
        description: str,
        source_type: str,
    ) -> FinancialTransactionModel:
        transaction = FinancialTransactionModel(
            business_unit_id=business_unit_id,
            direction=direction,
            transaction_type=transaction_type,
            amount=amount,
            currency="HUF",
            occurred_at=occurred_at,
            description=description,
            source_type=source_type,
            source_id=uuid4(),
        )
        self.db_session.add(transaction)
        self.db_session.commit()
        self.db_session.refresh(transaction)
        self.transaction_ids.append(transaction.id)
        return transaction

    def create_pos_row(
        self,
        *,
        business_unit_id,
        row_number: int,
        payload_date: date,
        occurred_at: datetime | None = None,
        receipt_no: str,
        category_name: str,
        product_name: str,
        quantity: Decimal,
        gross_amount: Decimal,
        payment_method: str = "cash",
    ) -> ImportRowModel:
        payload = {
            "date": payload_date.isoformat(),
            "receipt_no": receipt_no,
            "category_name": category_name,
            "product_name": product_name,
            "quantity": str(quantity),
            "gross_amount": str(gross_amount),
            "payment_method": payment_method,
        }
        if occurred_at is not None:
            payload["occurred_at"] = occurred_at.isoformat()

        batch = ImportBatchModel(
            business_unit_id=business_unit_id,
            import_type="pos_sales",
            status="parsed",
            started_at=datetime.now(UTC),
            finished_at=datetime.now(UTC),
            total_rows=1,
            parsed_rows=1,
            error_rows=0,
        )
        self.db_session.add(batch)
        self.db_session.flush()

        import_file = ImportFileModel(
            batch_id=batch.id,
            original_name=f"analytics-test-{uuid4().hex[:8]}.csv",
            stored_path=f"storage/imports/analytics-test-{uuid4().hex}.csv",
            mime_type="text/csv",
            size_bytes=128,
        )
        self.db_session.add(import_file)
        self.db_session.flush()

        row = ImportRowModel(
            batch_id=batch.id,
            file_id=import_file.id,
            row_number=row_number,
            raw_payload=payload,
            normalized_payload=payload,
            parse_status="parsed",
        )
        self.db_session.add(row)
        self.db_session.commit()
        self.db_session.refresh(row)

        self.batch_ids.append(batch.id)
        self.file_ids.append(import_file.id)
        self.row_ids.append(row.id)
        return row

    def create_inventory_item(
        self,
        *,
        business_unit_id,
        name: str,
        uom_id,
        default_unit_cost: Decimal,
    ) -> InventoryItemModel:
        item = InventoryItemModel(
            business_unit_id=business_unit_id,
            name=name,
            item_type="raw_material",
            uom_id=uom_id,
            track_stock=True,
            default_unit_cost=default_unit_cost,
            estimated_stock_quantity=None,
            is_active=True,
        )
        self.db_session.add(item)
        self.db_session.commit()
        self.db_session.refresh(item)
        self.inventory_item_ids.append(item.id)
        return item

    def create_inventory_movement(
        self,
        *,
        business_unit_id,
        inventory_item_id,
        uom_id,
        movement_type: str,
        quantity: Decimal,
    ) -> InventoryMovementModel:
        movement = InventoryMovementModel(
            business_unit_id=business_unit_id,
            inventory_item_id=inventory_item_id,
            movement_type=movement_type,
            quantity=quantity,
            uom_id=uom_id,
            unit_cost=Decimal("1"),
            note="Analytics product risk test",
            source_type="analytics_product_risk_test",
            source_id=uuid4(),
            occurred_at=datetime(2036, 5, 1, 10, 0, tzinfo=UTC),
        )
        self.db_session.add(movement)
        self.db_session.commit()
        self.db_session.refresh(movement)
        self.movement_ids.append(movement.id)
        return movement

    def create_product(
        self,
        *,
        business_unit_id,
        sales_uom_id,
        name: str,
        sale_price_gross: Decimal,
        default_unit_cost: Decimal | None = None,
        default_vat_rate_id=None,
        category_id=None,
    ) -> ProductModel:
        product = ProductModel(
            business_unit_id=business_unit_id,
            category_id=category_id,
            sales_uom_id=sales_uom_id,
            default_vat_rate_id=default_vat_rate_id,
            sku=f"RISK-{uuid4().hex[:8]}",
            name=name,
            product_type="finished_good",
            sale_price_gross=sale_price_gross,
            default_unit_cost=default_unit_cost,
            currency="HUF",
            is_active=True,
        )
        self.db_session.add(product)
        self.db_session.commit()
        self.db_session.refresh(product)
        self.product_ids.append(product.id)
        return product

    def create_category(
        self,
        *,
        business_unit_id,
        name: str,
    ) -> CategoryModel:
        category = CategoryModel(
            business_unit_id=business_unit_id,
            name=name,
            is_active=True,
        )
        self.db_session.add(category)
        self.db_session.commit()
        self.db_session.refresh(category)
        self.category_ids.append(category.id)
        return category

    def create_event(
        self,
        *,
        business_unit_id,
        title: str,
        starts_at: datetime,
        ends_at: datetime | None = None,
        status: str = "planned",
        performer_name: str | None = None,
        expected_attendance: int | None = None,
    ) -> EventModel:
        event = EventModel(
            business_unit_id=business_unit_id,
            location_id=None,
            title=title,
            status=status,
            starts_at=starts_at,
            ends_at=ends_at,
            performer_name=performer_name,
            expected_attendance=expected_attendance,
            ticket_revenue_gross=Decimal("0"),
            bar_revenue_gross=Decimal("0"),
            performer_share_percent=Decimal("80"),
            performer_fixed_fee=Decimal("0"),
            event_cost_amount=Decimal("0"),
            notes=None,
            is_active=True,
        )
        self.db_session.add(event)
        self.db_session.commit()
        self.db_session.refresh(event)
        self.event_ids.append(event.id)
        return event

    def create_recipe(
        self,
        *,
        product_id,
        yield_uom_id,
        ingredient_item_id,
        ingredient_uom_id,
        quantity: Decimal,
    ) -> None:
        recipe = RecipeModel(product_id=product_id, name=f"Recipe {uuid4().hex[:8]}", is_active=True)
        self.db_session.add(recipe)
        self.db_session.flush()
        version = RecipeVersionModel(
            recipe_id=recipe.id,
            version_no=1,
            is_active=True,
            yield_quantity=Decimal("1"),
            yield_uom_id=yield_uom_id,
            notes=None,
        )
        self.db_session.add(version)
        self.db_session.flush()
        ingredient = RecipeIngredientModel(
            recipe_version_id=version.id,
            inventory_item_id=ingredient_item_id,
            quantity=quantity,
            uom_id=ingredient_uom_id,
        )
        self.db_session.add(ingredient)
        self.db_session.commit()
        self.recipe_ids.append(recipe.id)
        self.recipe_version_ids.append(version.id)
        self.recipe_ingredient_ids.append(ingredient.id)

    def create_shared_weather_observation(
        self,
        *,
        observed_at: datetime,
        weather_condition: str,
        temperature_c: Decimal,
    ) -> WeatherObservationHourlyModel:
        location = self.db_session.scalar(
            select(WeatherLocationModel)
            .where(WeatherLocationModel.scope == "shared")
            .where(WeatherLocationModel.name == SHARED_WEATHER_LOCATION_NAME)
            .where(WeatherLocationModel.provider == SHARED_WEATHER_PROVIDER)
        )
        if location is None:
            location = WeatherLocationModel(
                business_unit_id=None,
                location_id=None,
                scope="shared",
                name=SHARED_WEATHER_LOCATION_NAME,
                latitude=SHARED_WEATHER_LATITUDE,
                longitude=SHARED_WEATHER_LONGITUDE,
                timezone=SHARED_WEATHER_TIMEZONE,
                provider=SHARED_WEATHER_PROVIDER,
                is_active=True,
            )
            self.db_session.add(location)
            self.db_session.commit()
            self.db_session.refresh(location)
            self.weather_location_ids.append(location.id)

        observation = WeatherObservationHourlyModel(
            weather_location_id=location.id,
            observed_at=observed_at.astimezone(UTC),
            provider=SHARED_WEATHER_PROVIDER,
            provider_model="analytics-test",
            weather_code=0,
            weather_condition=weather_condition,
            temperature_c=temperature_c,
            apparent_temperature_c=temperature_c,
            relative_humidity_percent=Decimal("50"),
            precipitation_mm=Decimal("0"),
            rain_mm=Decimal("0"),
            snowfall_cm=Decimal("0"),
            cloud_cover_percent=Decimal("10"),
            wind_speed_kmh=Decimal("6"),
            wind_gust_kmh=Decimal("12"),
            pressure_hpa=Decimal("1012"),
            source_payload={"source": "analytics-test"},
        )
        self.db_session.add(observation)
        self.db_session.commit()
        self.db_session.refresh(observation)
        self.weather_observation_ids.append(observation.id)
        return observation

    def create_shared_weather_forecast(
        self,
        *,
        forecasted_at: datetime,
        weather_condition: str,
        temperature_c: Decimal,
        precipitation_mm: Decimal = Decimal("0"),
        cloud_cover_percent: Decimal = Decimal("10"),
    ) -> WeatherForecastHourlyModel:
        location = self.db_session.scalar(
            select(WeatherLocationModel)
            .where(WeatherLocationModel.scope == "shared")
            .where(WeatherLocationModel.name == SHARED_WEATHER_LOCATION_NAME)
            .where(WeatherLocationModel.provider == SHARED_WEATHER_PROVIDER)
        )
        if location is None:
            location = WeatherLocationModel(
                business_unit_id=None,
                location_id=None,
                scope="shared",
                name=SHARED_WEATHER_LOCATION_NAME,
                latitude=SHARED_WEATHER_LATITUDE,
                longitude=SHARED_WEATHER_LONGITUDE,
                timezone=SHARED_WEATHER_TIMEZONE,
                provider=SHARED_WEATHER_PROVIDER,
                is_active=True,
            )
            self.db_session.add(location)
            self.db_session.commit()
            self.db_session.refresh(location)
            self.weather_location_ids.append(location.id)

        forecast = WeatherForecastHourlyModel(
            weather_location_id=location.id,
            forecasted_at=forecasted_at.astimezone(UTC),
            provider=SHARED_WEATHER_PROVIDER,
            provider_model="analytics-forecast-test",
            forecast_run_at=datetime.now(UTC),
            horizon_hours=24,
            weather_code=0,
            weather_condition=weather_condition,
            temperature_c=temperature_c,
            apparent_temperature_c=temperature_c,
            relative_humidity_percent=Decimal("50"),
            precipitation_mm=precipitation_mm,
            rain_mm=precipitation_mm,
            snowfall_cm=Decimal("0"),
            cloud_cover_percent=cloud_cover_percent,
            wind_speed_kmh=Decimal("6"),
            wind_gust_kmh=Decimal("12"),
            pressure_hpa=Decimal("1012"),
            source_payload={"source": "analytics-forecast-test"},
        )
        self.db_session.add(forecast)
        self.db_session.commit()
        self.db_session.refresh(forecast)
        self.weather_forecast_ids.append(forecast.id)
        return forecast

    def cleanup(self) -> None:
        self.db_session.rollback()
        if self.weather_forecast_ids:
            self.db_session.execute(
                delete(WeatherForecastHourlyModel).where(
                    WeatherForecastHourlyModel.id.in_(self.weather_forecast_ids)
                )
            )
        if self.weather_observation_ids:
            self.db_session.execute(
                delete(WeatherObservationHourlyModel).where(
                    WeatherObservationHourlyModel.id.in_(self.weather_observation_ids)
                )
            )
        if self.weather_location_ids:
            self.db_session.execute(
                delete(WeatherLocationModel).where(
                    WeatherLocationModel.id.in_(self.weather_location_ids)
                )
            )
        if self.recipe_ingredient_ids:
            self.db_session.execute(
                delete(RecipeIngredientModel).where(
                    RecipeIngredientModel.id.in_(self.recipe_ingredient_ids)
                )
            )
        if self.recipe_version_ids:
            self.db_session.execute(
                delete(RecipeVersionModel).where(
                    RecipeVersionModel.id.in_(self.recipe_version_ids)
                )
            )
        if self.recipe_ids:
            self.db_session.execute(
                delete(RecipeModel).where(RecipeModel.id.in_(self.recipe_ids))
            )
        if self.transaction_ids:
            self.db_session.execute(
                delete(FinancialTransactionModel).where(
                    FinancialTransactionModel.id.in_(self.transaction_ids)
                )
            )
        if self.movement_ids:
            self.db_session.execute(
                delete(InventoryMovementModel).where(
                    InventoryMovementModel.id.in_(self.movement_ids)
                )
            )
        if self.event_ids:
            self.db_session.execute(
                delete(EventModel).where(EventModel.id.in_(self.event_ids))
            )
        if self.product_ids:
            self.db_session.execute(
                delete(ProductModel).where(ProductModel.id.in_(self.product_ids))
            )
        if self.category_ids:
            self.db_session.execute(
                delete(CategoryModel).where(CategoryModel.id.in_(self.category_ids))
            )
        if self.inventory_item_ids:
            self.db_session.execute(
                delete(InventoryItemModel).where(
                    InventoryItemModel.id.in_(self.inventory_item_ids)
                )
            )
        if self.row_ids:
            self.db_session.execute(
                delete(ImportRowModel).where(ImportRowModel.id.in_(self.row_ids))
            )
        if self.file_ids:
            self.db_session.execute(
                delete(ImportFileModel).where(ImportFileModel.id.in_(self.file_ids))
            )
        if self.batch_ids:
            self.db_session.execute(
                delete(ImportBatchModel).where(ImportBatchModel.id.in_(self.batch_ids))
            )
        self.db_session.commit()


@pytest.fixture
def analytics_data_builder(db_session: Session):
    """Yield a dashboard test data builder with explicit cleanup."""

    builder = AnalyticsTestDataBuilder(db_session=db_session)
    try:
        yield builder
    finally:
        builder.cleanup()


@pytest.fixture
def flow_business_unit(db_session: Session) -> BusinessUnitModel:
    """Return the seeded Flow business unit."""

    business_unit = db_session.scalar(
        select(BusinessUnitModel).where(BusinessUnitModel.code == "flow")
    )
    if business_unit is None:
        raise RuntimeError("Expected seeded 'flow' business unit to exist.")
    return business_unit


def _kpi_value(payload: dict, code: str) -> Decimal:
    for kpi in payload["kpis"]:
        if kpi["code"] == code:
            return Decimal(str(kpi["value"]))
    raise AssertionError(f"Missing dashboard KPI: {code}")


def test_dashboard_returns_kpis_and_breakdowns_for_business_unit(
    client: TestClient,
    analytics_data_builder: AnalyticsTestDataBuilder,
    test_business_unit: BusinessUnitModel,
) -> None:
    business_date = date(2030, 1, 10)
    analytics_data_builder.create_transaction(
        business_unit_id=test_business_unit.id,
        direction="inflow",
        transaction_type="pos_sale",
        amount=Decimal("1000.00"),
        occurred_at=datetime(2030, 1, 10, 10, 0, tzinfo=UTC),
        description="Dashboard test revenue",
        source_type="analytics_test_revenue",
    )
    analytics_data_builder.create_transaction(
        business_unit_id=test_business_unit.id,
        direction="outflow",
        transaction_type="supplier_invoice",
        amount=Decimal("250.00"),
        occurred_at=datetime(2030, 1, 10, 12, 0, tzinfo=UTC),
        description="Dashboard test cost",
        source_type="analytics_test_cost",
    )
    analytics_data_builder.create_pos_row(
        business_unit_id=test_business_unit.id,
        row_number=2,
        payload_date=business_date,
        receipt_no="DASH-1001",
        category_name="Pastry",
        product_name="Croissant",
        quantity=Decimal("2"),
        gross_amount=Decimal("1000"),
    )

    response = client.get(
        f"{API_PREFIX}/dashboard",
        params={
            "scope": "overall",
            "business_unit_id": str(test_business_unit.id),
            "period": "custom",
            "start_date": "2030-01-01",
            "end_date": "2030-01-31",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["scope"] == "overall"
    assert payload["business_unit_id"] == str(test_business_unit.id)
    assert _kpi_value(payload, "revenue") == Decimal("1000.00")
    assert _kpi_value(payload, "cost") == Decimal("250.00")
    assert _kpi_value(payload, "profit") == Decimal("750.00")
    assert _kpi_value(payload, "estimated_cogs") == Decimal("0")
    assert _kpi_value(payload, "transaction_count") == Decimal("2")
    assert _kpi_value(payload, "profit_margin") == Decimal("1000.00")
    assert _kpi_value(payload, "gross_margin_percent") == Decimal("100.00")
    assert _kpi_value(payload, "average_basket_value") == Decimal("1000")
    assert _kpi_value(payload, "average_basket_quantity") == Decimal("2")
    assert payload["category_breakdown"][0]["label"] == "Pastry"
    assert Decimal(str(payload["category_breakdown"][0]["revenue"])) == Decimal("1000")
    assert payload["payment_method_breakdown"][0]["label"] == "cash"
    assert Decimal(str(payload["payment_method_breakdown"][0]["revenue"])) == Decimal("1000")
    assert payload["basket_value_distribution"][1]["label"] == "1000-2499"
    assert payload["basket_value_distribution"][1]["transaction_count"] == 1
    assert len(payload["traffic_heatmap"]) == 168
    assert "category_trends" in payload
    assert "forecast_preparation_insights" in payload
    assert "forecast_product_demand_insights" in payload
    assert "forecast_peak_time_insights" in payload
    assert "flow_forecast_event_insights" in payload
    assert "product_risks" in payload
    assert "stock_risks" in payload
    assert payload["top_products"][0]["label"] == "Croissant"
    assert payload["expense_breakdown"][0]["label"] == "supplier_invoice"


def test_dashboard_scope_filters_overall_flow_and_gourmand(
    client: TestClient,
    analytics_data_builder: AnalyticsTestDataBuilder,
    flow_business_unit: BusinessUnitModel,
    gourmand_business_unit: BusinessUnitModel,
) -> None:
    analytics_data_builder.create_transaction(
        business_unit_id=flow_business_unit.id,
        direction="inflow",
        transaction_type="pos_sale",
        amount=Decimal("110.00"),
        occurred_at=datetime(2031, 2, 3, 10, 0, tzinfo=UTC),
        description="Flow dashboard revenue",
        source_type="analytics_test_scope_flow",
    )
    analytics_data_builder.create_transaction(
        business_unit_id=gourmand_business_unit.id,
        direction="inflow",
        transaction_type="pos_sale",
        amount=Decimal("220.00"),
        occurred_at=datetime(2031, 2, 3, 10, 0, tzinfo=UTC),
        description="Gourmand dashboard revenue",
        source_type="analytics_test_scope_gourmand",
    )

    params = {
        "period": "custom",
        "start_date": "2031-02-01",
        "end_date": "2031-02-28",
    }
    overall_response = client.get(
        f"{API_PREFIX}/dashboard",
        params={**params, "scope": "overall"},
    )
    flow_response = client.get(
        f"{API_PREFIX}/dashboard",
        params={**params, "scope": "flow"},
    )
    gourmand_response = client.get(
        f"{API_PREFIX}/dashboard",
        params={**params, "scope": "gourmand"},
    )

    assert overall_response.status_code == 200
    assert flow_response.status_code == 200
    assert gourmand_response.status_code == 200
    assert _kpi_value(overall_response.json(), "revenue") == Decimal("330.00")
    assert _kpi_value(flow_response.json(), "revenue") == Decimal("110.00")
    assert flow_response.json()["business_unit_id"] == str(flow_business_unit.id)
    assert _kpi_value(gourmand_response.json(), "revenue") == Decimal("220.00")
    assert gourmand_response.json()["business_unit_id"] == str(gourmand_business_unit.id)


def test_dashboard_period_presets_resolve_year_and_last_30_days(
    client: TestClient,
    analytics_data_builder: AnalyticsTestDataBuilder,
    test_business_unit: BusinessUnitModel,
) -> None:
    today = datetime.now(UTC).date()
    analytics_data_builder.create_transaction(
        business_unit_id=test_business_unit.id,
        direction="inflow",
        transaction_type="pos_sale",
        amount=Decimal("123.00"),
        occurred_at=datetime.combine(today, datetime.min.time(), tzinfo=UTC),
        description="Current period revenue",
        source_type="analytics_test_period",
    )

    year_response = client.get(
        f"{API_PREFIX}/dashboard",
        params={
            "scope": "overall",
            "business_unit_id": str(test_business_unit.id),
            "period": "year",
        },
    )
    last_30_days_response = client.get(
        f"{API_PREFIX}/dashboard",
        params={
            "scope": "overall",
            "business_unit_id": str(test_business_unit.id),
            "period": "last_30_days",
        },
    )

    assert year_response.status_code == 200
    assert year_response.json()["period"]["grain"] == "month"
    assert _kpi_value(year_response.json(), "revenue") == Decimal("123.00")
    assert last_30_days_response.status_code == 200
    assert last_30_days_response.json()["period"]["grain"] == "day"
    assert _kpi_value(last_30_days_response.json(), "revenue") == Decimal("123.00")


def test_dashboard_hour_preset_uses_current_hour_window(
    client: TestClient,
    analytics_data_builder: AnalyticsTestDataBuilder,
    test_business_unit: BusinessUnitModel,
) -> None:
    now = datetime.now(UTC)
    recent = now - timedelta(minutes=30)
    older = now - timedelta(hours=2)

    analytics_data_builder.create_transaction(
        business_unit_id=test_business_unit.id,
        direction="inflow",
        transaction_type="pos_sale",
        amount=Decimal("900.00"),
        occurred_at=recent,
        description="Recent hourly revenue",
        source_type="analytics_test_hour_recent",
    )
    analytics_data_builder.create_transaction(
        business_unit_id=test_business_unit.id,
        direction="inflow",
        transaction_type="pos_sale",
        amount=Decimal("300.00"),
        occurred_at=older,
        description="Older hourly revenue",
        source_type="analytics_test_hour_older",
    )
    analytics_data_builder.create_pos_row(
        business_unit_id=test_business_unit.id,
        row_number=1,
        payload_date=recent.date(),
        occurred_at=recent,
        receipt_no="HOUR-1001",
        category_name="Coffee",
        product_name="Flat white",
        quantity=Decimal("1"),
        gross_amount=Decimal("900"),
    )

    response = client.get(
        f"{API_PREFIX}/dashboard",
        params={
            "scope": "overall",
            "business_unit_id": str(test_business_unit.id),
            "period": "last_1_hour",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["period"]["grain"] == "hour"
    assert _kpi_value(payload, "revenue") == Decimal("900.00")
    assert _kpi_value(payload, "average_basket_value") == Decimal("900")
    assert all("T" in point["period_start"] for point in payload["revenue_trend"])


def test_dashboard_category_and_product_drill_down_use_import_rows(
    client: TestClient,
    analytics_data_builder: AnalyticsTestDataBuilder,
    test_business_unit: BusinessUnitModel,
) -> None:
    analytics_data_builder.create_pos_row(
        business_unit_id=test_business_unit.id,
        row_number=2,
        payload_date=date(2032, 3, 4),
        receipt_no="DASH-2001",
        category_name="Pastry",
        product_name="Croissant",
        quantity=Decimal("2"),
        gross_amount=Decimal("1200"),
    )
    analytics_data_builder.create_pos_row(
        business_unit_id=test_business_unit.id,
        row_number=3,
        payload_date=date(2032, 3, 4),
        receipt_no="DASH-2002",
        category_name="Coffee",
        product_name="Espresso",
        quantity=Decimal("1"),
        gross_amount=Decimal("750"),
    )

    common_params = {
        "scope": "overall",
        "business_unit_id": str(test_business_unit.id),
        "period": "custom",
        "start_date": "2032-03-01",
        "end_date": "2032-03-31",
    }
    categories_response = client.get(
        f"{API_PREFIX}/dashboard/categories",
        params=common_params,
    )
    products_response = client.get(
        f"{API_PREFIX}/dashboard/products",
        params={**common_params, "category_name": "Pastry"},
    )

    assert categories_response.status_code == 200
    categories = categories_response.json()
    assert [row["label"] for row in categories] == ["Pastry", "Coffee"]
    assert categories[0]["source_layer"] == "import_derived"

    assert products_response.status_code == 200
    products = products_response.json()
    assert len(products) == 1
    assert products[0]["product_name"] == "Croissant"
    assert products[0]["category_name"] == "Pastry"
    assert Decimal(str(products[0]["revenue"])) == Decimal("1200")
    assert products[0]["source_layer"] == "import_derived"


def test_dashboard_product_source_rows_return_pos_import_rows(
    client: TestClient,
    analytics_data_builder: AnalyticsTestDataBuilder,
    test_business_unit: BusinessUnitModel,
) -> None:
    source_row = analytics_data_builder.create_pos_row(
        business_unit_id=test_business_unit.id,
        row_number=7,
        payload_date=date(2032, 5, 6),
        receipt_no="DASH-2501",
        category_name="Pastry",
        product_name="Croissant",
        quantity=Decimal("3"),
        gross_amount=Decimal("1800"),
    )
    analytics_data_builder.create_pos_row(
        business_unit_id=test_business_unit.id,
        row_number=8,
        payload_date=date(2032, 5, 6),
        receipt_no="DASH-2502",
        category_name="Coffee",
        product_name="Espresso",
        quantity=Decimal("1"),
        gross_amount=Decimal("750"),
    )

    response = client.get(
        f"{API_PREFIX}/dashboard/product-rows",
        params={
            "scope": "overall",
            "business_unit_id": str(test_business_unit.id),
            "period": "custom",
            "start_date": "2032-05-01",
            "end_date": "2032-05-31",
            "category_name": "Pastry",
            "product_name": "Croissant",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["row_id"] == str(source_row.id)
    assert payload[0]["row_number"] == 7
    assert payload[0]["date"] == "2032-05-06"
    assert payload[0]["receipt_no"] == "DASH-2501"
    assert payload[0]["category_name"] == "Pastry"
    assert payload[0]["product_name"] == "Croissant"
    assert Decimal(str(payload[0]["quantity"])) == Decimal("3")
    assert Decimal(str(payload[0]["gross_amount"])) == Decimal("1800")
    assert payload[0]["source_layer"] == "import_derived"


def test_dashboard_pos_revenue_tax_breakdown_is_derived_from_product_vat(
    client: TestClient,
    db_session: Session,
    analytics_data_builder: AnalyticsTestDataBuilder,
    test_business_unit: BusinessUnitModel,
) -> None:
    vat_rate = db_session.scalar(select(VatRateModel).where(VatRateModel.code == "HU_27"))
    assert vat_rate is not None
    analytics_data_builder.create_product(
        business_unit_id=test_business_unit.id,
        sales_uom_id=None,
        name="VAT Croissant",
        sale_price_gross=Decimal("1270"),
        default_unit_cost=Decimal("400"),
        default_vat_rate_id=vat_rate.id,
    )
    source_row = analytics_data_builder.create_pos_row(
        business_unit_id=test_business_unit.id,
        row_number=9,
        payload_date=date(2032, 6, 7),
        receipt_no="DASH-2601",
        category_name="Pastry",
        product_name="VAT Croissant",
        quantity=Decimal("1"),
        gross_amount=Decimal("1270"),
    )
    analytics_data_builder.create_pos_row(
        business_unit_id=test_business_unit.id,
        row_number=10,
        payload_date=date(2032, 6, 8),
        receipt_no="DASH-2602",
        category_name="Beverage",
        product_name="Missing VAT Soda",
        quantity=Decimal("1"),
        gross_amount=Decimal("127"),
    )

    common_params = {
        "scope": "overall",
        "business_unit_id": str(test_business_unit.id),
        "period": "custom",
        "start_date": "2032-06-01",
        "end_date": "2032-06-30",
    }
    categories_response = client.get(
        f"{API_PREFIX}/dashboard/categories",
        params=common_params,
    )
    products_response = client.get(
        f"{API_PREFIX}/dashboard/products",
        params={**common_params, "category_name": "Pastry"},
    )
    source_response = client.get(
        f"{API_PREFIX}/dashboard/product-rows",
        params={**common_params, "category_name": "Pastry", "product_name": "VAT Croissant"},
    )
    dashboard_response = client.get(
        f"{API_PREFIX}/dashboard",
        params=common_params,
    )

    assert categories_response.status_code == 200
    category = categories_response.json()[0]
    assert category["label"] == "Pastry"
    assert Decimal(str(category["revenue"])) == Decimal("1270")
    assert Decimal(str(category["net_revenue"])) == Decimal("1000.00")
    assert Decimal(str(category["vat_amount"])) == Decimal("270.00")
    assert category["amount_basis"] == "gross"
    assert category["tax_breakdown_source"] == "product_vat_derived"

    assert products_response.status_code == 200
    product = products_response.json()[0]
    assert product["product_name"] == "VAT Croissant"
    assert Decimal(str(product["net_revenue"])) == Decimal("1000.00")
    assert Decimal(str(product["vat_amount"])) == Decimal("270.00")
    assert Decimal(str(product["estimated_unit_cost_net"])) == Decimal("400")
    assert Decimal(str(product["estimated_cogs_net"])) == Decimal("400")
    assert Decimal(str(product["estimated_net_margin_amount"])) == Decimal("600.00")
    assert Decimal(str(product["estimated_margin_percent"])) == Decimal("60.0")
    assert product["tax_breakdown_source"] == "product_vat_derived"
    assert product["cost_source"] == "recipe_or_unit_cost"
    assert product["margin_status"] == "complete"

    assert source_response.status_code == 200
    source_payload = source_response.json()
    assert len(source_payload) == 1
    assert source_payload[0]["row_id"] == str(source_row.id)
    assert Decimal(str(source_payload[0]["net_amount"])) == Decimal("1000.00")
    assert Decimal(str(source_payload[0]["vat_amount"])) == Decimal("270.00")
    assert Decimal(str(source_payload[0]["vat_rate_percent"])) == Decimal("27.0000")
    assert source_payload[0]["tax_breakdown_source"] == "product_vat_derived"

    assert dashboard_response.status_code == 200
    readiness = dashboard_response.json()["vat_readiness"]
    assert readiness["status"] == "partial"
    assert Decimal(str(readiness["coverage_percent"])) == Decimal("90.91")
    assert Decimal(str(readiness["gross_revenue"])) == Decimal("1397")
    assert Decimal(str(readiness["covered_gross_revenue"])) == Decimal("1270")
    assert Decimal(str(readiness["missing_gross_revenue"])) == Decimal("127")
    assert readiness["total_row_count"] == 2
    assert readiness["covered_row_count"] == 1
    assert readiness["missing_row_count"] == 1
    assert readiness["tax_breakdown_source"] == "partial_product_vat_derived"


def test_dashboard_expense_drill_down_returns_financial_actual_rows(
    client: TestClient,
    analytics_data_builder: AnalyticsTestDataBuilder,
    test_business_unit: BusinessUnitModel,
) -> None:
    expense_transaction = analytics_data_builder.create_transaction(
        business_unit_id=test_business_unit.id,
        direction="outflow",
        transaction_type="supplier_invoice",
        amount=Decimal("4500.00"),
        occurred_at=datetime(2033, 4, 5, 9, 0, tzinfo=UTC),
        description="Supplier invoice DASH-3001",
        source_type="supplier_invoice",
    )
    analytics_data_builder.create_transaction(
        business_unit_id=test_business_unit.id,
        direction="inflow",
        transaction_type="pos_sale",
        amount=Decimal("9000.00"),
        occurred_at=datetime(2033, 4, 5, 10, 0, tzinfo=UTC),
        description="Revenue control row",
        source_type="analytics_test_revenue_control",
    )

    response = client.get(
        f"{API_PREFIX}/dashboard/expenses",
        params={
            "scope": "overall",
            "business_unit_id": str(test_business_unit.id),
            "period": "custom",
            "start_date": "2033-04-01",
            "end_date": "2033-04-30",
            "transaction_type": "supplier_invoice",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["transaction_id"] == str(expense_transaction.id)
    assert payload[0]["transaction_type"] == "supplier_invoice"
    assert Decimal(str(payload[0]["amount"])) == Decimal("4500.00")
    assert payload[0]["source_type"] == "supplier_invoice"
    assert payload[0]["source_layer"] == "financial_actual"


def test_dashboard_expense_source_returns_supplier_invoice_lines(
    client: TestClient,
    test_business_unit: BusinessUnitModel,
    test_unit_of_measure,
    create_supplier,
    create_inventory_item,
    create_purchase_invoice,
) -> None:
    supplier = create_supplier(
        business_unit_id=test_business_unit.id,
        name="Dashboard Source Supplier",
    )
    inventory_item = create_inventory_item(
        business_unit_id=test_business_unit.id,
        uom_id=test_unit_of_measure.id,
        name="Dashboard Source Flour",
        item_type="raw_material",
    )
    invoice = create_purchase_invoice(
        business_unit_id=test_business_unit.id,
        supplier_id=supplier.id,
        invoice_number="DASH-SOURCE-001",
        invoice_date=date(2034, 6, 7),
        currency="HUF",
        gross_total=Decimal("5600.00"),
        notes="Dashboard source drill-down invoice",
        lines=[
            {
                "inventory_item_id": inventory_item.id,
                "description": "Flour 10 kg",
                "quantity": Decimal("10.000"),
                "uom_id": test_unit_of_measure.id,
                "unit_net_amount": Decimal("500.00"),
                "line_net_amount": Decimal("5000.00"),
            },
            {
                "description": "Delivery fee",
                "quantity": Decimal("1.000"),
                "uom_id": test_unit_of_measure.id,
                "unit_net_amount": Decimal("600.00"),
                "line_net_amount": Decimal("600.00"),
            },
        ],
    )
    post_response = client.post(f"/api/v1/procurement/purchase-invoices/{invoice.id}/post")
    assert post_response.status_code == 200

    expenses_response = client.get(
        f"{API_PREFIX}/dashboard/expenses",
        params={
            "scope": "overall",
            "business_unit_id": str(test_business_unit.id),
            "period": "custom",
            "start_date": "2034-06-01",
            "end_date": "2034-06-30",
            "transaction_type": "supplier_invoice",
        },
    )
    assert expenses_response.status_code == 200
    expense_row = expenses_response.json()[0]

    source_response = client.get(
        f"{API_PREFIX}/dashboard/expense-source",
        params={"transaction_id": expense_row["transaction_id"]},
    )

    assert source_response.status_code == 200
    payload = source_response.json()
    assert payload["transaction_id"] == expense_row["transaction_id"]
    assert payload["source_type"] == "supplier_invoice"
    assert payload["source_id"] == str(invoice.id)
    assert payload["supplier_id"] == str(supplier.id)
    assert payload["supplier_name"] == "Dashboard Source Supplier"
    assert payload["invoice_number"] == "DASH-SOURCE-001"
    assert payload["invoice_date"] == "2034-06-07"
    assert Decimal(str(payload["gross_total"])) == Decimal("5600.00")
    assert len(payload["lines"]) == 2
    assert {line["description"] for line in payload["lines"]} == {
        "Delivery fee",
        "Flour 10 kg",
    }


def test_dashboard_basket_pairs_return_co_purchased_products(
    client: TestClient,
    analytics_data_builder: AnalyticsTestDataBuilder,
    test_business_unit: BusinessUnitModel,
) -> None:
    for row_number, receipt_no, product_name, amount in [
        (2, "BASKET-1001", "Croissant", Decimal("1200")),
        (3, "BASKET-1001", "Espresso", Decimal("750")),
        (4, "BASKET-1001", "Macaron", Decimal("900")),
        (5, "BASKET-1002", "Croissant", Decimal("1200")),
        (6, "BASKET-1002", "Espresso", Decimal("750")),
    ]:
        analytics_data_builder.create_pos_row(
            business_unit_id=test_business_unit.id,
            row_number=row_number,
            payload_date=date(2035, 7, 8),
            receipt_no=receipt_no,
            category_name="Dashboard Basket",
            product_name=product_name,
            quantity=Decimal("1"),
            gross_amount=amount,
        )

    response = client.get(
        f"{API_PREFIX}/dashboard/basket-pairs",
        params={
            "scope": "overall",
            "business_unit_id": str(test_business_unit.id),
            "period": "custom",
            "start_date": "2035-07-01",
            "end_date": "2035-07-31",
            "limit": 5,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 3
    assert payload[0]["product_a"] == "Croissant"
    assert payload[0]["product_b"] == "Espresso"
    assert payload[0]["basket_count"] == 2
    assert Decimal(str(payload[0]["total_gross_amount"])) == Decimal("3900")
    assert payload[0]["source_layer"] == "import_derived"


def test_dashboard_basket_pair_receipts_return_source_receipts(
    client: TestClient,
    analytics_data_builder: AnalyticsTestDataBuilder,
    test_business_unit: BusinessUnitModel,
) -> None:
    for row_number, receipt_no, product_name, amount in [
        (2, "BASKET-DETAIL-1", "Croissant", Decimal("1200")),
        (3, "BASKET-DETAIL-1", "Espresso", Decimal("750")),
        (4, "BASKET-DETAIL-1", "Macaron", Decimal("900")),
        (5, "BASKET-DETAIL-2", "Croissant", Decimal("1200")),
        (6, "BASKET-DETAIL-2", "Tea", Decimal("650")),
    ]:
        analytics_data_builder.create_pos_row(
            business_unit_id=test_business_unit.id,
            row_number=row_number,
            payload_date=date(2035, 8, 9),
            receipt_no=receipt_no,
            category_name="Dashboard Basket Detail",
            product_name=product_name,
            quantity=Decimal("1"),
            gross_amount=amount,
        )

    response = client.get(
        f"{API_PREFIX}/dashboard/basket-pair-receipts",
        params={
            "scope": "overall",
            "business_unit_id": str(test_business_unit.id),
            "period": "custom",
            "start_date": "2035-08-01",
            "end_date": "2035-08-31",
            "product_a": "Croissant",
            "product_b": "Espresso",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["receipt_no"] == "BASKET-DETAIL-1"
    assert payload[0]["date"] == "2035-08-09"
    assert Decimal(str(payload[0]["gross_amount"])) == Decimal("2850")
    assert Decimal(str(payload[0]["quantity"])) == Decimal("3")
    assert {line["product_name"] for line in payload[0]["lines"]} == {
        "Croissant",
        "Espresso",
        "Macaron",
    }
    assert payload[0]["source_layer"] == "import_derived"


def test_dashboard_returns_payment_method_breakdown(
    client: TestClient,
    analytics_data_builder: AnalyticsTestDataBuilder,
    test_business_unit: BusinessUnitModel,
) -> None:
    analytics_data_builder.create_pos_row(
        business_unit_id=test_business_unit.id,
        row_number=1,
        payload_date=date(2036, 1, 5),
        receipt_no="PAYMENT-1",
        category_name="Coffee",
        product_name="Espresso",
        quantity=Decimal("1"),
        gross_amount=Decimal("700"),
        payment_method="card",
    )
    analytics_data_builder.create_pos_row(
        business_unit_id=test_business_unit.id,
        row_number=2,
        payload_date=date(2036, 1, 5),
        receipt_no="PAYMENT-2",
        category_name="Pastry",
        product_name="Croissant",
        quantity=Decimal("1"),
        gross_amount=Decimal("1200"),
        payment_method="cash",
    )
    analytics_data_builder.create_pos_row(
        business_unit_id=test_business_unit.id,
        row_number=3,
        payload_date=date(2036, 1, 5),
        receipt_no="PAYMENT-3",
        category_name="Pastry",
        product_name="Macaron",
        quantity=Decimal("2"),
        gross_amount=Decimal("900"),
        payment_method="card",
    )

    response = client.get(
        f"{API_PREFIX}/dashboard",
        params={
            "scope": "overall",
            "business_unit_id": str(test_business_unit.id),
            "period": "custom",
            "start_date": "2036-01-01",
            "end_date": "2036-01-31",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    payment_rows = payload["payment_method_breakdown"]
    assert [row["label"] for row in payment_rows] == ["card", "cash"]
    assert Decimal(str(payment_rows[0]["revenue"])) == Decimal("1600")
    assert Decimal(str(payment_rows[1]["revenue"])) == Decimal("1200")
    assert payment_rows[0]["transaction_count"] == 2


def test_dashboard_returns_basket_value_distribution(
    client: TestClient,
    analytics_data_builder: AnalyticsTestDataBuilder,
    test_business_unit: BusinessUnitModel,
) -> None:
    for row_number, receipt_no, amount in [
        (1, "BASKET-VALUE-1", Decimal("700")),
        (2, "BASKET-VALUE-2", Decimal("1200")),
        (3, "BASKET-VALUE-2", Decimal("500")),
        (4, "BASKET-VALUE-3", Decimal("3500")),
        (5, "BASKET-VALUE-4", Decimal("11000")),
    ]:
        analytics_data_builder.create_pos_row(
            business_unit_id=test_business_unit.id,
            row_number=row_number,
            payload_date=date(2036, 2, 6),
            receipt_no=receipt_no,
            category_name="Basket Bands",
            product_name=f"Product {row_number}",
            quantity=Decimal("1"),
            gross_amount=amount,
            payment_method="card",
        )

    response = client.get(
        f"{API_PREFIX}/dashboard",
        params={
            "scope": "overall",
            "business_unit_id": str(test_business_unit.id),
            "period": "custom",
            "start_date": "2036-02-01",
            "end_date": "2036-02-28",
        },
    )

    assert response.status_code == 200
    distribution = response.json()["basket_value_distribution"]
    by_label = {row["label"]: row for row in distribution}
    assert by_label["0-999"]["transaction_count"] == 1
    assert Decimal(str(by_label["0-999"]["revenue"])) == Decimal("700")
    assert by_label["1000-2499"]["transaction_count"] == 1
    assert Decimal(str(by_label["1000-2499"]["revenue"])) == Decimal("1700")
    assert by_label["2500-4999"]["transaction_count"] == 1
    assert by_label["10000+"]["transaction_count"] == 1


def test_dashboard_returns_traffic_heatmap(
    client: TestClient,
    analytics_data_builder: AnalyticsTestDataBuilder,
    test_business_unit: BusinessUnitModel,
) -> None:
    local_monday = datetime(2036, 3, 3, 10, 15, tzinfo=APP_TIME_ZONE)
    local_tuesday = datetime(2036, 3, 4, 11, 30, tzinfo=APP_TIME_ZONE)
    for row_number, occurred_at, amount in [
        (1, local_monday, Decimal("900")),
        (2, local_monday.replace(minute=45), Decimal("600")),
        (3, local_tuesday, Decimal("1200")),
    ]:
        analytics_data_builder.create_pos_row(
            business_unit_id=test_business_unit.id,
            row_number=row_number,
            payload_date=occurred_at.date(),
            occurred_at=occurred_at,
            receipt_no=f"HEAT-{row_number}",
            category_name="Heatmap",
            product_name=f"Heat product {row_number}",
            quantity=Decimal("1"),
            gross_amount=amount,
            payment_method="card",
        )

    response = client.get(
        f"{API_PREFIX}/dashboard",
        params={
            "scope": "overall",
            "business_unit_id": str(test_business_unit.id),
            "period": "custom",
            "start_date": "2036-03-01",
            "end_date": "2036-03-31",
        },
    )

    assert response.status_code == 200
    cells = response.json()["traffic_heatmap"]
    assert len(cells) == 168

    by_slot = {(cell["weekday"], cell["hour"]): cell for cell in cells}
    monday_cell = by_slot[(0, 10)]
    tuesday_cell = by_slot[(1, 11)]
    assert monday_cell["transaction_count"] == 2
    assert Decimal(str(monday_cell["revenue"])) == Decimal("1500")
    assert tuesday_cell["transaction_count"] == 1
    assert Decimal(str(tuesday_cell["revenue"])) == Decimal("1200")
    assert by_slot[(6, 23)]["transaction_count"] == 0


def test_dashboard_returns_category_trends(
    client: TestClient,
    analytics_data_builder: AnalyticsTestDataBuilder,
    test_business_unit: BusinessUnitModel,
) -> None:
    rows = [
        (1, date(2036, 4, 2), "Coffee", Decimal("1"), Decimal("1000")),
        (2, date(2036, 4, 9), "Coffee", Decimal("1"), Decimal("1800")),
        (3, date(2036, 4, 3), "Bakery", Decimal("2"), Decimal("2000")),
        (4, date(2036, 4, 10), "Bakery", Decimal("1"), Decimal("500")),
        (5, date(2036, 4, 11), "New category", Decimal("1"), Decimal("300")),
    ]
    for row_number, payload_date, category_name, quantity, gross_amount in rows:
        analytics_data_builder.create_pos_row(
            business_unit_id=test_business_unit.id,
            row_number=row_number,
            payload_date=payload_date,
            occurred_at=datetime(
                payload_date.year,
                payload_date.month,
                payload_date.day,
                12,
                0,
                tzinfo=APP_TIME_ZONE,
            ),
            receipt_no=f"TREND-{row_number}",
            category_name=category_name,
            product_name=f"{category_name} product",
            quantity=quantity,
            gross_amount=gross_amount,
            payment_method="card",
        )

    response = client.get(
        f"{API_PREFIX}/dashboard",
        params={
            "scope": "overall",
            "business_unit_id": str(test_business_unit.id),
            "period": "custom",
            "start_date": "2036-04-08",
            "end_date": "2036-04-14",
        },
    )

    assert response.status_code == 200
    trends = response.json()["category_trends"]
    by_label = {row["label"]: row for row in trends}
    coffee = by_label["Coffee"]
    bakery = by_label["Bakery"]
    new_category = by_label["New category"]

    assert Decimal(str(coffee["current_revenue"])) == Decimal("1800")
    assert Decimal(str(coffee["previous_revenue"])) == Decimal("1000")
    assert Decimal(str(coffee["revenue_change"])) == Decimal("800")
    assert Decimal(str(coffee["revenue_change_percent"])) == Decimal("80.0")
    assert coffee["current_transaction_count"] == 1

    assert Decimal(str(bakery["revenue_change"])) == Decimal("-1500")
    assert Decimal(str(bakery["revenue_change_percent"])) == Decimal("-75.00")
    assert bakery["previous_transaction_count"] == 1

    assert Decimal(str(new_category["previous_revenue"])) == Decimal("0")
    assert Decimal(str(new_category["revenue_change_percent"])) == Decimal("100")


def test_dashboard_returns_weather_category_insights(
    client: TestClient,
    analytics_data_builder: AnalyticsTestDataBuilder,
    gourmand_business_unit: BusinessUnitModel,
) -> None:
    sale_time = datetime(2036, 7, 12, 10, 15, tzinfo=APP_TIME_ZONE)
    analytics_data_builder.create_shared_weather_observation(
        observed_at=sale_time.replace(minute=0, second=0, microsecond=0),
        weather_condition="napos",
        temperature_c=Decimal("27.50"),
    )
    analytics_data_builder.create_pos_row(
        business_unit_id=gourmand_business_unit.id,
        row_number=1,
        payload_date=sale_time.date(),
        occurred_at=sale_time,
        receipt_no="WEATHER-1",
        category_name="Fagyi",
        product_name="Vanilia fagyi",
        quantity=Decimal("2"),
        gross_amount=Decimal("1800"),
        payment_method="card",
    )
    analytics_data_builder.create_pos_row(
        business_unit_id=gourmand_business_unit.id,
        row_number=2,
        payload_date=sale_time.date(),
        occurred_at=sale_time.replace(minute=45),
        receipt_no="WEATHER-2",
        category_name="Fagyi",
        product_name="Csoki fagyi",
        quantity=Decimal("1"),
        gross_amount=Decimal("900"),
        payment_method="cash",
    )

    response = client.get(
        f"{API_PREFIX}/dashboard",
        params={
            "scope": "overall",
            "period": "custom",
            "start_date": "2036-07-01",
            "end_date": "2036-07-31",
        },
    )

    assert response.status_code == 200
    insights = response.json()["weather_category_insights"]
    assert len(insights) == 1
    row = insights[0]
    assert row["category_name"] == "Fagyi"
    assert row["weather_condition"] == "napos"
    assert Decimal(str(row["revenue"])) == Decimal("2700")
    assert Decimal(str(row["quantity"])) == Decimal("3")
    assert row["transaction_count"] == 2
    assert Decimal(str(row["average_temperature_c"])) == Decimal("27.50")
    assert row["source_layer"] == "weather_enriched_import"

    temperature_rows = response.json()["temperature_band_insights"]
    assert len(temperature_rows) == 1
    temperature_row = temperature_rows[0]
    assert temperature_row["temperature_band"] == "meleg"
    assert Decimal(str(temperature_row["revenue"])) == Decimal("2700")
    assert Decimal(str(temperature_row["quantity"])) == Decimal("3")
    assert temperature_row["transaction_count"] == 2
    assert temperature_row["basket_count"] == 2
    assert Decimal(str(temperature_row["average_basket_value"])) == Decimal("1350")
    assert Decimal(str(temperature_row["average_temperature_c"])) == Decimal("27.50")
    assert temperature_row["top_category_name"] == "Fagyi"
    assert Decimal(str(temperature_row["top_category_revenue"])) == Decimal("2700")

    condition_rows = response.json()["weather_condition_insights"]
    assert len(condition_rows) == 1
    condition_row = condition_rows[0]
    assert condition_row["condition_band"] == "napos_szaraz"
    assert Decimal(str(condition_row["revenue"])) == Decimal("2700")
    assert Decimal(str(condition_row["quantity"])) == Decimal("3")
    assert condition_row["transaction_count"] == 2
    assert condition_row["basket_count"] == 2
    assert Decimal(str(condition_row["average_basket_value"])) == Decimal("1350")
    assert Decimal(str(condition_row["average_cloud_cover_percent"])) == Decimal("10")
    assert Decimal(str(condition_row["precipitation_mm"])) == Decimal("0")
    assert condition_row["top_category_name"] == "Fagyi"
    assert Decimal(str(condition_row["top_category_revenue"])) == Decimal("2700")


def test_dashboard_returns_forecast_impact_insights(
    client: TestClient,
    analytics_data_builder: AnalyticsTestDataBuilder,
    test_business_unit: BusinessUnitModel,
) -> None:
    now = datetime.now(APP_TIME_ZONE)
    historical_time = datetime(2020, 1, 11, 10, 42, tzinfo=APP_TIME_ZONE)
    forecast_time = (now + timedelta(days=2)).replace(
        hour=10,
        minute=17,
        second=0,
        microsecond=0,
    )

    analytics_data_builder.create_shared_weather_observation(
        observed_at=historical_time.replace(minute=17),
        weather_condition="napos",
        temperature_c=Decimal("29.00"),
    )
    analytics_data_builder.create_pos_row(
        business_unit_id=test_business_unit.id,
        row_number=1,
        payload_date=historical_time.date(),
        occurred_at=historical_time,
        receipt_no="FORECAST-HIST-1",
        category_name="Fagyi",
        product_name="Vanilia fagyi",
        quantity=Decimal("2"),
        gross_amount=Decimal("2400"),
        payment_method="card",
    )
    analytics_data_builder.create_shared_weather_forecast(
        forecasted_at=forecast_time,
        weather_condition="napos",
        temperature_c=Decimal("30.00"),
    )
    analytics_data_builder.create_shared_weather_forecast(
        forecasted_at=forecast_time + timedelta(hours=1),
        weather_condition="napos",
        temperature_c=Decimal("31.00"),
    )

    response = client.get(
        f"{API_PREFIX}/dashboard",
        params={
            "scope": "overall",
            "business_unit_id": str(test_business_unit.id),
            "period": "custom",
            "start_date": historical_time.date().isoformat(),
            "end_date": historical_time.date().isoformat(),
        },
    )

    assert response.status_code == 200
    rows = response.json()["forecast_impact_insights"]
    forecast_row = next(
        row for row in rows if row["forecast_date"] == forecast_time.date().isoformat()
    )
    assert forecast_row["forecast_hours"] >= 2
    assert Decimal(str(forecast_row["expected_revenue"])) == Decimal("2400")
    assert forecast_row["confidence"] in {"magas", "kozepes", "alacsony"}
    assert forecast_row["source_layer"] == "weather_forecast_cache"
    assert forecast_row["recommendation"]


def test_dashboard_returns_gourmand_forecast_category_demand(
    client: TestClient,
    analytics_data_builder: AnalyticsTestDataBuilder,
    test_business_unit: BusinessUnitModel,
) -> None:
    now = datetime.now(APP_TIME_ZONE)
    historical_time = datetime(2020, 2, 8, 11, 10, tzinfo=APP_TIME_ZONE)
    forecast_time = (now + timedelta(days=3)).replace(
        hour=11,
        minute=37,
        second=0,
        microsecond=0,
    )

    analytics_data_builder.create_shared_weather_observation(
        observed_at=historical_time,
        weather_condition="napos",
        temperature_c=Decimal("30.00"),
    )
    analytics_data_builder.create_pos_row(
        business_unit_id=test_business_unit.id,
        row_number=1,
        payload_date=historical_time.date(),
        occurred_at=historical_time,
        receipt_no="FORECAST-CAT-1",
        category_name="Fagyi",
        product_name="Citrom fagyi",
        quantity=Decimal("5"),
        gross_amount=Decimal("5000"),
        payment_method="card",
    )
    analytics_data_builder.create_pos_row(
        business_unit_id=test_business_unit.id,
        row_number=2,
        payload_date=historical_time.date(),
        occurred_at=historical_time,
        receipt_no="FORECAST-CAT-2",
        category_name="Kave",
        product_name="Espresso",
        quantity=Decimal("2"),
        gross_amount=Decimal("1200"),
        payment_method="cash",
    )
    analytics_data_builder.create_shared_weather_forecast(
        forecasted_at=forecast_time,
        weather_condition="napos",
        temperature_c=Decimal("31.00"),
    )

    response = client.get(
        f"{API_PREFIX}/dashboard",
        params={
            "scope": "overall",
            "business_unit_id": str(test_business_unit.id),
            "period": "custom",
            "start_date": historical_time.date().isoformat(),
            "end_date": historical_time.date().isoformat(),
        },
    )

    assert response.status_code == 200
    rows = response.json()["forecast_category_demand_insights"]
    forecast_rows = [
        row
        for row in rows
        if row["forecast_date"] == forecast_time.date().isoformat()
    ]
    assert [row["category_name"] for row in forecast_rows[:2]] == ["Fagyi", "Kave"]
    fagyi = forecast_rows[0]
    assert Decimal(str(fagyi["expected_revenue"])) == Decimal("5000")
    assert Decimal(str(fagyi["expected_quantity"])) == Decimal("5")
    assert fagyi["confidence"] in {"magas", "kozepes", "alacsony"}
    assert fagyi["source_layer"] == "weather_forecast_category_model"
    assert fagyi["recommendation"]


def test_dashboard_returns_gourmand_product_and_peak_time_forecasts(
    client: TestClient,
    analytics_data_builder: AnalyticsTestDataBuilder,
    test_business_unit: BusinessUnitModel,
) -> None:
    now = datetime.now(APP_TIME_ZONE)
    historical_time = datetime(2020, 4, 18, 14, 15, tzinfo=APP_TIME_ZONE)
    forecast_time = (now + timedelta(days=5)).replace(
        hour=14,
        minute=35,
        second=0,
        microsecond=0,
    )

    analytics_data_builder.create_shared_weather_observation(
        observed_at=historical_time,
        weather_condition="napos",
        temperature_c=Decimal("30.00"),
    )
    analytics_data_builder.create_pos_row(
        business_unit_id=test_business_unit.id,
        row_number=1,
        payload_date=historical_time.date(),
        occurred_at=historical_time,
        receipt_no="FORECAST-PRODUCT-1",
        category_name="Termek Fagyi",
        product_name="Termek mangó fagyi",
        quantity=Decimal("4"),
        gross_amount=Decimal("4800"),
        payment_method="card",
    )
    analytics_data_builder.create_pos_row(
        business_unit_id=test_business_unit.id,
        row_number=2,
        payload_date=historical_time.date(),
        occurred_at=historical_time + timedelta(minutes=15),
        receipt_no="FORECAST-PRODUCT-2",
        category_name="Termek Süti",
        product_name="Termek isler",
        quantity=Decimal("2"),
        gross_amount=Decimal("1800"),
        payment_method="cash",
    )
    analytics_data_builder.create_shared_weather_forecast(
        forecasted_at=forecast_time,
        weather_condition="napos",
        temperature_c=Decimal("31.00"),
    )

    response = client.get(
        f"{API_PREFIX}/dashboard",
        params={
            "scope": "overall",
            "business_unit_id": str(test_business_unit.id),
            "period": "custom",
            "start_date": historical_time.date().isoformat(),
            "end_date": historical_time.date().isoformat(),
        },
    )

    assert response.status_code == 200
    payload = response.json()

    product_rows = [
        row
        for row in payload["forecast_product_demand_insights"]
        if row["forecast_date"] == forecast_time.date().isoformat()
    ]
    mango = next(row for row in product_rows if row["product_name"] == "Termek mangó fagyi")
    assert mango["category_name"] == "Termek Fagyi"
    assert Decimal(str(mango["expected_revenue"])) == Decimal("4800")
    assert Decimal(str(mango["expected_quantity"])) == Decimal("4")
    assert mango["source_layer"] == "weather_forecast_product_model"
    assert mango["recommendation"]

    peak_rows = [
        row
        for row in payload["forecast_peak_time_insights"]
        if row["forecast_date"] == forecast_time.date().isoformat()
    ]
    delutan = next(row for row in peak_rows if row["time_window"] == "Délután")
    assert delutan["start_hour"] == 13
    assert delutan["end_hour"] == 17
    assert Decimal(str(delutan["expected_revenue"])) == Decimal("6600")
    assert Decimal(str(delutan["expected_quantity"])) == Decimal("6")
    assert delutan["expected_transaction_count"] == 2
    assert delutan["source_layer"] == "weather_forecast_peak_time_model"
    assert delutan["recommendation"]


def test_dashboard_returns_gourmand_forecast_preparation_insights(
    client: TestClient,
    analytics_data_builder: AnalyticsTestDataBuilder,
    test_business_unit: BusinessUnitModel,
    pcs_unit_of_measure: UnitOfMeasureModel,
) -> None:
    now = datetime.now(APP_TIME_ZONE)
    historical_time = datetime(2020, 3, 14, 10, 20, tzinfo=APP_TIME_ZONE)
    forecast_time = (now + timedelta(days=4)).replace(
        hour=10,
        minute=22,
        second=0,
        microsecond=0,
    )
    category = analytics_data_builder.create_category(
        business_unit_id=test_business_unit.id,
        name="Prep Fagyi",
    )
    ingredient = analytics_data_builder.create_inventory_item(
        business_unit_id=test_business_unit.id,
        name="Prep fagyi alap",
        uom_id=pcs_unit_of_measure.id,
        default_unit_cost=Decimal("100"),
    )
    analytics_data_builder.create_inventory_movement(
        business_unit_id=test_business_unit.id,
        inventory_item_id=ingredient.id,
        uom_id=pcs_unit_of_measure.id,
        movement_type="initial_stock",
        quantity=Decimal("1"),
    )
    product = analytics_data_builder.create_product(
        business_unit_id=test_business_unit.id,
        sales_uom_id=pcs_unit_of_measure.id,
        category_id=category.id,
        name="Prep citrom fagyi",
        sale_price_gross=Decimal("1200"),
    )
    analytics_data_builder.create_recipe(
        product_id=product.id,
        yield_uom_id=pcs_unit_of_measure.id,
        ingredient_item_id=ingredient.id,
        ingredient_uom_id=pcs_unit_of_measure.id,
        quantity=Decimal("2"),
    )
    analytics_data_builder.create_shared_weather_observation(
        observed_at=historical_time,
        weather_condition="napos",
        temperature_c=Decimal("30.00"),
    )
    analytics_data_builder.create_pos_row(
        business_unit_id=test_business_unit.id,
        row_number=1,
        payload_date=historical_time.date(),
        occurred_at=historical_time,
        receipt_no="FORECAST-PREP-1",
        category_name="Prep Fagyi",
        product_name="Prep citrom fagyi",
        quantity=Decimal("5"),
        gross_amount=Decimal("6000"),
        payment_method="card",
    )
    analytics_data_builder.create_shared_weather_forecast(
        forecasted_at=forecast_time,
        weather_condition="napos",
        temperature_c=Decimal("31.00"),
    )

    response = client.get(
        f"{API_PREFIX}/dashboard",
        params={
            "scope": "overall",
            "business_unit_id": str(test_business_unit.id),
            "period": "custom",
            "start_date": historical_time.date().isoformat(),
            "end_date": historical_time.date().isoformat(),
        },
    )

    assert response.status_code == 200
    rows = response.json()["forecast_preparation_insights"]
    prep_row = next(
        row
        for row in rows
        if row["category_name"] == "Prep Fagyi"
        and row["forecast_date"] == forecast_time.date().isoformat()
    )
    assert prep_row["forecast_date"] == forecast_time.date().isoformat()
    assert prep_row["product_count"] == 1
    assert prep_row["risky_product_count"] == 1
    assert prep_row["low_stock_ingredient_count"] == 1
    assert prep_row["missing_stock_ingredient_count"] == 0
    assert prep_row["readiness_level"] == "figyelendo"
    assert prep_row["source_layer"] == "weather_forecast_catalog_inventory_model"
    assert prep_row["recommendation"]


def test_dashboard_returns_flow_forecast_event_insights(
    client: TestClient,
    analytics_data_builder: AnalyticsTestDataBuilder,
    flow_business_unit: BusinessUnitModel,
) -> None:
    now = datetime.now(APP_TIME_ZONE)
    event_start = (now + timedelta(days=3)).replace(
        hour=20,
        minute=10,
        second=0,
        microsecond=0,
    )
    event_end = event_start + timedelta(hours=3)
    event = analytics_data_builder.create_event(
        business_unit_id=flow_business_unit.id,
        title="Forecast teszt koncert",
        starts_at=event_start,
        ends_at=event_end,
        status="planned",
        performer_name="Forecast zenekar",
        expected_attendance=260,
    )
    analytics_data_builder.create_shared_weather_forecast(
        forecasted_at=event_start.replace(minute=22),
        weather_condition="esos",
        temperature_c=Decimal("12.00"),
        precipitation_mm=Decimal("2.50"),
        cloud_cover_percent=Decimal("90"),
    )
    analytics_data_builder.create_shared_weather_forecast(
        forecasted_at=(event_start + timedelta(hours=1)).replace(minute=22),
        weather_condition="esos",
        temperature_c=Decimal("11.00"),
        precipitation_mm=Decimal("1.20"),
        cloud_cover_percent=Decimal("90"),
    )

    response = client.get(
        f"{API_PREFIX}/dashboard",
        params={
            "scope": "flow",
            "business_unit_id": str(flow_business_unit.id),
            "period": "custom",
            "start_date": now.date().isoformat(),
            "end_date": (now + timedelta(days=7)).date().isoformat(),
        },
    )

    assert response.status_code == 200
    rows = response.json()["flow_forecast_event_insights"]
    event_row = next(row for row in rows if row["event_id"] == str(event.id))
    assert event_row["title"] == "Forecast teszt koncert"
    assert event_row["forecast_hours"] >= 2
    assert event_row["dominant_condition_band"] == "csapadekos"
    assert event_row["preparation_level"] == "kritikus"
    assert event_row["focus_area"] == "Beléptetés, ruhatár és fedett sor"
    assert event_row["source_layer"] == "weather_forecast_event_model"
    assert event_row["recommendation"]


def test_dashboard_returns_product_risks(
    client: TestClient,
    analytics_data_builder: AnalyticsTestDataBuilder,
    test_business_unit: BusinessUnitModel,
    pcs_unit_of_measure: UnitOfMeasureModel,
) -> None:
    low_stock_item = analytics_data_builder.create_inventory_item(
        business_unit_id=test_business_unit.id,
        name="Risk test empty ingredient",
        uom_id=pcs_unit_of_measure.id,
        default_unit_cost=Decimal("350"),
    )
    missing_stock_item = analytics_data_builder.create_inventory_item(
        business_unit_id=test_business_unit.id,
        name="Risk test missing stock ingredient",
        uom_id=pcs_unit_of_measure.id,
        default_unit_cost=Decimal("200"),
    )
    analytics_data_builder.create_inventory_movement(
        business_unit_id=test_business_unit.id,
        inventory_item_id=low_stock_item.id,
        uom_id=pcs_unit_of_measure.id,
        movement_type="initial_stock",
        quantity=Decimal("0"),
    )
    negative_margin_product = analytics_data_builder.create_product(
        business_unit_id=test_business_unit.id,
        sales_uom_id=pcs_unit_of_measure.id,
        name="Risk test negative margin product",
        sale_price_gross=Decimal("100"),
        default_unit_cost=Decimal("250"),
    )
    low_stock_product = analytics_data_builder.create_product(
        business_unit_id=test_business_unit.id,
        sales_uom_id=pcs_unit_of_measure.id,
        name="Risk test low stock recipe",
        sale_price_gross=Decimal("1000"),
    )
    missing_stock_product = analytics_data_builder.create_product(
        business_unit_id=test_business_unit.id,
        sales_uom_id=pcs_unit_of_measure.id,
        name="Risk test missing stock recipe",
        sale_price_gross=Decimal("1000"),
    )
    analytics_data_builder.create_recipe(
        product_id=low_stock_product.id,
        yield_uom_id=pcs_unit_of_measure.id,
        ingredient_item_id=low_stock_item.id,
        ingredient_uom_id=pcs_unit_of_measure.id,
        quantity=Decimal("1"),
    )
    analytics_data_builder.create_recipe(
        product_id=missing_stock_product.id,
        yield_uom_id=pcs_unit_of_measure.id,
        ingredient_item_id=missing_stock_item.id,
        ingredient_uom_id=pcs_unit_of_measure.id,
        quantity=Decimal("1"),
    )

    response = client.get(
        f"{API_PREFIX}/dashboard",
        params={
            "scope": "overall",
            "business_unit_id": str(test_business_unit.id),
            "period": "custom",
            "start_date": "2036-05-01",
            "end_date": "2036-05-31",
        },
    )

    assert response.status_code == 200
    risks = response.json()["product_risks"]
    by_name = {row["product_name"]: row for row in risks}

    negative = by_name["Risk test negative margin product"]
    assert negative["risk_level"] == "danger"
    assert "Negatív árrés" in negative["risk_reasons"]
    assert Decimal(str(negative["estimated_margin_amount"])) == Decimal("-150")

    low_stock = by_name["Risk test low stock recipe"]
    assert "Alapanyaghiány" in low_stock["risk_reasons"]
    assert low_stock["low_stock_ingredient_count"] == 1

    missing_stock = by_name["Risk test missing stock recipe"]
    assert "Hiányzó készletadat" in missing_stock["risk_reasons"]
    assert missing_stock["missing_stock_ingredient_count"] == 1


def test_dashboard_returns_stock_risks(
    client: TestClient,
    analytics_data_builder: AnalyticsTestDataBuilder,
    test_business_unit: BusinessUnitModel,
    pcs_unit_of_measure: UnitOfMeasureModel,
) -> None:
    no_stock_item = analytics_data_builder.create_inventory_item(
        business_unit_id=test_business_unit.id,
        name="Risk test stock missing movement",
        uom_id=pcs_unit_of_measure.id,
        default_unit_cost=Decimal("120"),
    )
    low_stock_item = analytics_data_builder.create_inventory_item(
        business_unit_id=test_business_unit.id,
        name="Risk test stock low usage",
        uom_id=pcs_unit_of_measure.id,
        default_unit_cost=Decimal("80"),
    )
    analytics_data_builder.create_inventory_movement(
        business_unit_id=test_business_unit.id,
        inventory_item_id=low_stock_item.id,
        uom_id=pcs_unit_of_measure.id,
        movement_type="initial_stock",
        quantity=Decimal("1"),
    )

    no_stock_product = analytics_data_builder.create_product(
        business_unit_id=test_business_unit.id,
        sales_uom_id=pcs_unit_of_measure.id,
        name="Risk test no stock product",
        sale_price_gross=Decimal("900"),
    )
    low_stock_product_a = analytics_data_builder.create_product(
        business_unit_id=test_business_unit.id,
        sales_uom_id=pcs_unit_of_measure.id,
        name="Risk test low stock product A",
        sale_price_gross=Decimal("900"),
    )
    low_stock_product_b = analytics_data_builder.create_product(
        business_unit_id=test_business_unit.id,
        sales_uom_id=pcs_unit_of_measure.id,
        name="Risk test low stock product B",
        sale_price_gross=Decimal("900"),
    )
    analytics_data_builder.create_recipe(
        product_id=no_stock_product.id,
        yield_uom_id=pcs_unit_of_measure.id,
        ingredient_item_id=no_stock_item.id,
        ingredient_uom_id=pcs_unit_of_measure.id,
        quantity=Decimal("1"),
    )
    for product in (low_stock_product_a, low_stock_product_b):
        analytics_data_builder.create_recipe(
            product_id=product.id,
            yield_uom_id=pcs_unit_of_measure.id,
            ingredient_item_id=low_stock_item.id,
            ingredient_uom_id=pcs_unit_of_measure.id,
            quantity=Decimal("1"),
        )

    response = client.get(
        f"{API_PREFIX}/dashboard",
        params={
            "scope": "overall",
            "business_unit_id": str(test_business_unit.id),
            "period": "custom",
            "start_date": "2036-06-01",
            "end_date": "2036-06-30",
        },
    )

    assert response.status_code == 200
    risks = response.json()["stock_risks"]
    by_name = {row["item_name"]: row for row in risks}

    missing = by_name["Risk test stock missing movement"]
    assert missing["risk_level"] == "danger"
    assert missing["current_quantity"] == "0"
    assert "Nincs készletmozgás" in missing["risk_reasons"]
    assert "Nincs tényleges készlet" in missing["risk_reasons"]
    assert missing["used_by_product_count"] == 1

    low = by_name["Risk test stock low usage"]
    assert low["risk_level"] == "warning"
    assert Decimal(str(low["current_quantity"])) == Decimal("1")
    assert "Alacsony készlet recept-használathoz képest" in low["risk_reasons"]
    assert low["used_by_product_count"] == 2
