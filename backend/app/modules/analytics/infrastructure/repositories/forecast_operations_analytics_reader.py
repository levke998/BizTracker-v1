"""Operational forecast analytics for production readiness and Flow events."""

from __future__ import annotations

import uuid
from collections import defaultdict
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.analytics.domain.entities.dashboard_snapshot import (
    DashboardFlowForecastEventRow,
    DashboardForecastCategoryDemandRow,
    DashboardForecastPreparationRow,
)
from app.modules.analytics.infrastructure.repositories.forecast_analytics_reader import (
    ForecastAnalyticsReader,
    forecast_condition_band,
    forecast_precipitation,
)
from app.modules.analytics.infrastructure.repositories.forecast_demand_rules import (
    average_decimal,
    dominant_label,
)
from app.modules.analytics.infrastructure.repositories.weather_analytics_reader import (
    hour_start_utc,
)
from app.modules.events.infrastructure.orm.event_model import EventModel
from app.modules.master_data.infrastructure.orm.category_model import CategoryModel
from app.modules.master_data.infrastructure.orm.product_model import ProductModel


class ForecastOperationsAnalyticsReader:
    """Build forecast-driven production and event preparation read models."""

    def __init__(
        self,
        session: Session,
        *,
        forecast_reader: ForecastAnalyticsReader,
        time_zone: ZoneInfo,
        horizon_days: int,
    ) -> None:
        self._session = session
        self._forecast_reader = forecast_reader
        self._time_zone = time_zone
        self._horizon_days = horizon_days

    def build_preparation(
        self,
        *,
        business_unit_id: uuid.UUID | None,
        scope: str,
        demand_rows: list[DashboardForecastCategoryDemandRow],
        recipe_ingredients: dict[uuid.UUID, list[Any]],
        stock_levels: dict[uuid.UUID, dict[str, Any]],
        limit: int,
    ) -> list[DashboardForecastPreparationRow]:
        if scope == "flow" or not demand_rows:
            return []

        products_by_category = self._active_products_by_category(
            business_unit_id=business_unit_id
        )
        result: list[DashboardForecastPreparationRow] = []
        for demand in demand_rows:
            products = products_by_category.get(demand.category_name.casefold(), [])
            if not products:
                result.append(self._unmapped_preparation_row(demand))
                continue

            expected_per_product = demand.expected_quantity / Decimal(len(products))
            risky_products = 0
            low_stock = 0
            missing_stock = 0
            for product in products:
                ingredients = recipe_ingredients.get(product.id, [])
                product_has_risk = False
                if not ingredients and product.default_unit_cost is None:
                    risky_products += 1
                    continue
                for ingredient in ingredients:
                    stock = stock_levels.get(ingredient.inventory_item_id)
                    if stock is None or int(stock["movement_count"]) == 0:
                        missing_stock += 1
                        product_has_risk = True
                        continue
                    current = Decimal(stock["current_quantity"])
                    required = Decimal(ingredient.quantity) * max(
                        expected_per_product,
                        Decimal("1"),
                    )
                    if current <= Decimal("0"):
                        missing_stock += 1
                        product_has_risk = True
                    elif current < required:
                        low_stock += 1
                        product_has_risk = True
                if product_has_risk:
                    risky_products += 1

            readiness = preparation_readiness(
                demand_signal=demand.demand_signal,
                confidence=demand.confidence,
                product_count=len(products),
                risky_product_count=risky_products,
                low_stock_count=low_stock,
                missing_stock_count=missing_stock,
            )
            result.append(
                DashboardForecastPreparationRow(
                    forecast_date=demand.forecast_date,
                    category_name=demand.category_name,
                    expected_revenue=demand.expected_revenue,
                    expected_quantity=demand.expected_quantity,
                    demand_signal=demand.demand_signal,
                    confidence=demand.confidence,
                    product_count=len(products),
                    risky_product_count=risky_products,
                    low_stock_ingredient_count=low_stock,
                    missing_stock_ingredient_count=missing_stock,
                    readiness_level=readiness,
                    recommendation=preparation_recommendation(
                        category_name=demand.category_name,
                        demand_signal=demand.demand_signal,
                        readiness_level=readiness,
                        risky_product_count=risky_products,
                        low_stock_count=low_stock,
                        missing_stock_count=missing_stock,
                    ),
                    source_layer="weather_forecast_catalog_inventory_model",
                )
            )
        return sorted(
            result,
            key=lambda row: (
                row.forecast_date,
                -readiness_rank(row.readiness_level),
                -row.expected_revenue,
            ),
        )[:limit]

    def build_flow_events(
        self,
        *,
        business_unit_id: uuid.UUID | None,
        scope: str,
        limit: int,
    ) -> list[DashboardFlowForecastEventRow]:
        if scope != "flow" or business_unit_id is None:
            return []
        now = datetime.now(self._time_zone)
        forecast_end = now + timedelta(days=self._horizon_days)
        events = self._list_events(
            business_unit_id=business_unit_id,
            starts_from=now,
            starts_to=forecast_end,
            limit=limit,
        )
        if not events:
            return []
        forecasts = self._forecast_reader.list_forecasts(
            start_at=now,
            end_at=forecast_end + timedelta(hours=8),
        )
        by_hour = {
            hour_start_utc(forecast.forecasted_at): forecast
            for forecast in forecasts
        }
        return [
            self._build_event_row(
                event=event,
                starts_at=self._as_app_time(event.starts_at),
                ends_at=(
                    self._as_app_time(event.ends_at)
                    if event.ends_at is not None
                    else self._as_app_time(event.starts_at) + timedelta(hours=8)
                ),
                forecasts=self._forecast_reader.event_window(
                    forecasts_by_hour=by_hour,
                    starts_at=self._as_app_time(event.starts_at),
                    ends_at=(
                        self._as_app_time(event.ends_at)
                        if event.ends_at is not None
                        else self._as_app_time(event.starts_at) + timedelta(hours=8)
                    ),
                ),
            )
            for event in events
        ]

    def _active_products_by_category(
        self,
        *,
        business_unit_id: uuid.UUID | None,
    ) -> dict[str, list[ProductModel]]:
        statement = (
            select(ProductModel, CategoryModel.name)
            .outerjoin(CategoryModel, ProductModel.category_id == CategoryModel.id)
            .where(ProductModel.is_active.is_(True))
            .order_by(ProductModel.name.asc())
        )
        if business_unit_id is not None:
            statement = statement.where(
                ProductModel.business_unit_id == business_unit_id
            )
        result: dict[str, list[ProductModel]] = defaultdict(list)
        for product, category_name in self._session.execute(statement).all():
            if category_name:
                result[str(category_name).casefold()].append(product)
        return dict(result)

    def _list_events(
        self,
        *,
        business_unit_id: uuid.UUID,
        starts_from: datetime,
        starts_to: datetime,
        limit: int,
    ) -> list[EventModel]:
        statement = (
            select(EventModel)
            .where(EventModel.business_unit_id == business_unit_id)
            .where(EventModel.is_active.is_(True))
            .where(EventModel.status.in_(("planned", "confirmed")))
            .where(EventModel.starts_at >= starts_from)
            .where(EventModel.starts_at <= starts_to)
            .order_by(EventModel.starts_at.asc())
            .limit(limit)
        )
        return list(self._session.scalars(statement).all())

    def _build_event_row(
        self,
        *,
        event: EventModel,
        starts_at: datetime,
        ends_at: datetime,
        forecasts: list[Any],
    ) -> DashboardFlowForecastEventRow:
        if not forecasts:
            return DashboardFlowForecastEventRow(
                event_id=event.id,
                title=event.title,
                performer_name=event.performer_name,
                starts_at=starts_at,
                ends_at=ends_at,
                expected_attendance=event.expected_attendance,
                forecast_hours=0,
                dominant_condition_band="ismeretlen",
                average_temperature_c=None,
                precipitation_mm=Decimal("0"),
                average_wind_speed_kmh=None,
                preparation_level="figyelendo",
                focus_area="Forecast lefedettség",
                recommendation=(
                    "Ehhez az event-idősávhoz még nincs forecast cache. "
                    "A következő szinkron után a jelzés automatikusan pontosodik."
                ),
                source_layer="weather_forecast_event_model",
            )

        conditions: dict[str, int] = defaultdict(int)
        temperatures: list[Decimal] = []
        winds: list[Decimal] = []
        precipitation = Decimal("0")
        for forecast in forecasts:
            conditions[forecast_condition_band(forecast)] += 1
            if forecast.temperature_c is not None:
                temperatures.append(Decimal(forecast.temperature_c))
            if forecast.wind_speed_kmh is not None:
                winds.append(Decimal(forecast.wind_speed_kmh))
            precipitation += forecast_precipitation(forecast)
        average_temperature = average_decimal(temperatures)
        average_wind = average_decimal(winds)
        condition = dominant_label(conditions, fallback="ismeretlen")
        level = flow_event_preparation_level(
            condition_band=condition,
            precipitation=precipitation,
            average_wind=average_wind,
            expected_attendance=event.expected_attendance,
        )
        return DashboardFlowForecastEventRow(
            event_id=event.id,
            title=event.title,
            performer_name=event.performer_name,
            starts_at=starts_at,
            ends_at=ends_at,
            expected_attendance=event.expected_attendance,
            forecast_hours=len(forecasts),
            dominant_condition_band=condition,
            average_temperature_c=average_temperature,
            precipitation_mm=precipitation,
            average_wind_speed_kmh=average_wind,
            preparation_level=level,
            focus_area=flow_event_focus_area(
                condition_band=condition,
                average_temperature=average_temperature,
                precipitation=precipitation,
                average_wind=average_wind,
                expected_attendance=event.expected_attendance,
            ),
            recommendation=flow_event_recommendation(
                title=event.title,
                condition_band=condition,
                average_temperature=average_temperature,
                precipitation=precipitation,
                average_wind=average_wind,
                expected_attendance=event.expected_attendance,
                preparation_level=level,
            ),
            source_layer="weather_forecast_event_model",
        )

    def _unmapped_preparation_row(
        self,
        demand: DashboardForecastCategoryDemandRow,
    ) -> DashboardForecastPreparationRow:
        return DashboardForecastPreparationRow(
            forecast_date=demand.forecast_date,
            category_name=demand.category_name,
            expected_revenue=demand.expected_revenue,
            expected_quantity=demand.expected_quantity,
            demand_signal=demand.demand_signal,
            confidence=demand.confidence,
            product_count=0,
            risky_product_count=0,
            low_stock_ingredient_count=0,
            missing_stock_ingredient_count=0,
            readiness_level="figyelendo",
            recommendation=(
                "Van kategória-előrejelzés, de nincs stabil katalóguskapcsolat. "
                "A termékeket recept- és készletadatokkal kell összekötni."
            ),
            source_layer="weather_forecast_catalog_inventory_model",
        )

    def _as_app_time(self, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=self._time_zone)
        return value.astimezone(self._time_zone)


def preparation_readiness(
    *,
    demand_signal: str,
    confidence: str,
    product_count: int,
    risky_product_count: int,
    low_stock_count: int,
    missing_stock_count: int,
) -> str:
    if missing_stock_count > 0 or (
        product_count > 0
        and risky_product_count >= product_count
        and low_stock_count == 0
    ):
        return "kritikus"
    if low_stock_count > 0 or demand_signal == "emelkedo" or confidence == "alacsony":
        return "figyelendo"
    return "rendben"


def readiness_rank(readiness_level: str) -> int:
    return {"kritikus": 3, "figyelendo": 2, "rendben": 1}.get(
        readiness_level,
        0,
    )


def preparation_recommendation(
    *,
    category_name: str,
    demand_signal: str,
    readiness_level: str,
    risky_product_count: int,
    low_stock_count: int,
    missing_stock_count: int,
) -> str:
    if missing_stock_count > 0:
        return f"{category_name}: {missing_stock_count} alapanyagnál hiányzik vagy nulla a készlet."
    if low_stock_count > 0:
        return f"{category_name}: {low_stock_count} alapanyag alacsony készleten áll."
    if risky_product_count > 0:
        return f"{category_name}: {risky_product_count} terméknél hiányos a recept vagy költségalap."
    if demand_signal == "emelkedo":
        return f"{category_name}: érdemes korábban indítani az előkészítést."
    if readiness_level == "rendben":
        return f"{category_name}: nincs kiemelt előkészítési kockázat."
    return f"{category_name}: normál előkészítés javasolt."


def flow_event_preparation_level(
    *,
    condition_band: str,
    precipitation: Decimal,
    average_wind: Decimal | None,
    expected_attendance: int | None,
) -> str:
    attendance = expected_attendance or 0
    wind = average_wind or Decimal("0")
    if precipitation >= Decimal("2") or (
        condition_band == "csapadekos" and attendance >= 200
    ):
        return "kritikus"
    if wind >= Decimal("28") or attendance >= 300:
        return "kritikus"
    if condition_band in {"csapadekos", "borult"}:
        return "figyelendo"
    if wind >= Decimal("20") or attendance >= 180:
        return "figyelendo"
    return "rendben"


def flow_event_focus_area(
    *,
    condition_band: str,
    average_temperature: Decimal | None,
    precipitation: Decimal,
    average_wind: Decimal | None,
    expected_attendance: int | None,
) -> str:
    wind = average_wind or Decimal("0")
    if condition_band == "csapadekos" or precipitation > Decimal("0"):
        return "Beléptetés, ruhatár és fedett sor"
    if wind >= Decimal("20"):
        return "Kültéri sor és biztonság"
    if average_temperature is not None and average_temperature <= Decimal("8"):
        return "Ruhatár és érkezési ritmus"
    if average_temperature is not None and average_temperature >= Decimal("27"):
        return "Hűtött ital és bárpult"
    if (expected_attendance or 0) >= 180:
        return "Személyzet és pultkapacitás"
    return "Normál event előkészítés"


def flow_event_recommendation(
    *,
    title: str,
    condition_band: str,
    average_temperature: Decimal | None,
    precipitation: Decimal,
    average_wind: Decimal | None,
    expected_attendance: int | None,
    preparation_level: str,
) -> str:
    if condition_band == "csapadekos" or precipitation > Decimal("0"):
        return f"{title}: fedett sor, ruhatár és gyors pultnyitás legyen előkészítve."
    if (average_wind or Decimal("0")) >= Decimal("20"):
        return f"{title}: a kültéri sor és biztonsági útvonalak ellenőrzése javasolt."
    if average_temperature is not None and average_temperature <= Decimal("8"):
        return f"{title}: ruhatár, meleg ital és érkezési csúcsidő legyen fókuszban."
    if average_temperature is not None and average_temperature >= Decimal("27"):
        return f"{title}: hideg ital, víz és gyors bárpult-kapacitás javasolt."
    if (expected_attendance or 0) >= 180:
        return f"{title}: a pult- és személyzeti kapacitást érdemes előre ellenőrizni."
    if preparation_level == "rendben":
        return f"{title}: normál eventterv elegendő."
    return f"{title}: a forecast jelzése figyelendő."
