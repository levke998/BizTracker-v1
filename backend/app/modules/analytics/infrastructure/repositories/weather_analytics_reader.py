"""Historical weather-enriched analytics queries and read-model mapping."""

from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.analytics.domain.entities.dashboard_snapshot import (
    DashboardTemperatureBandInsightRow,
    DashboardWeatherCategoryInsightRow,
    DashboardWeatherConditionInsightRow,
)
from app.modules.imports.infrastructure.orm.import_row_model import ImportRowModel
from app.modules.weather.infrastructure.orm.weather_model import (
    WeatherLocationModel,
    WeatherObservationHourlyModel,
)


class WeatherAnalyticsReader:
    """Enrich normalized POS rows with persisted hourly weather observations."""

    def __init__(
        self,
        session: Session,
        *,
        time_zone: ZoneInfo,
        location_name: str,
        provider: str,
        unknown_category: str,
    ) -> None:
        self._session = session
        self._time_zone = time_zone
        self._location_name = location_name
        self._provider = provider
        self._unknown_category = unknown_category

    def build_category_insights(
        self,
        *,
        rows: list[ImportRowModel],
        start_at: datetime,
        end_at: datetime,
        limit: int,
    ) -> list[DashboardWeatherCategoryInsightRow]:
        weather_by_hour = self._weather_by_hour(start_at=start_at, end_at=end_at)
        if not weather_by_hour:
            return []

        aggregate: dict[tuple[str, str], dict[str, Decimal | int]] = defaultdict(
            lambda: {
                "revenue": Decimal("0"),
                "quantity": Decimal("0"),
                "count": 0,
                "temperature_sum": Decimal("0"),
                "temperature_count": 0,
            }
        )
        for row in rows:
            payload = row.normalized_payload or {}
            occurred_at = self._payload_occurred_at(payload)
            if occurred_at is None or occurred_at < start_at or occurred_at > end_at:
                continue

            observation = weather_by_hour.get(hour_start_utc(occurred_at))
            if observation is None:
                continue

            category_name = self._extract_text(
                payload.get("category_name"),
                fallback=self._unknown_category,
            )
            key = (category_name, observation.weather_condition)
            aggregate[key]["revenue"] += self._parse_decimal(
                payload.get("gross_amount")
            )
            aggregate[key]["quantity"] += self._parse_decimal(payload.get("quantity"))
            aggregate[key]["count"] += 1
            if observation.temperature_c is not None:
                aggregate[key]["temperature_sum"] += Decimal(observation.temperature_c)
                aggregate[key]["temperature_count"] += 1

        insight_rows = [
            DashboardWeatherCategoryInsightRow(
                category_name=category_name,
                weather_condition=weather_condition,
                revenue=Decimal(values["revenue"]),
                quantity=Decimal(values["quantity"]),
                transaction_count=int(values["count"]),
                average_temperature_c=(
                    Decimal(values["temperature_sum"])
                    / Decimal(int(values["temperature_count"]))
                    if int(values["temperature_count"]) > 0
                    else None
                ),
                source_layer="weather_enriched_import",
            )
            for (category_name, weather_condition), values in aggregate.items()
        ]
        return sorted(
            insight_rows,
            key=lambda item: (item.revenue, item.transaction_count),
            reverse=True,
        )[:limit]

    def build_temperature_band_insights(
        self,
        *,
        rows: list[ImportRowModel],
        start_at: datetime,
        end_at: datetime,
    ) -> list[DashboardTemperatureBandInsightRow]:
        weather_by_hour = self._weather_by_hour(start_at=start_at, end_at=end_at)
        if not weather_by_hour:
            return []

        aggregate: dict[str, dict[str, Any]] = defaultdict(
            lambda: {
                "revenue": Decimal("0"),
                "quantity": Decimal("0"),
                "count": 0,
                "baskets": defaultdict(Decimal),
                "temperature_sum": Decimal("0"),
                "temperature_count": 0,
                "categories": defaultdict(Decimal),
            }
        )
        for row in rows:
            payload = row.normalized_payload or {}
            occurred_at = self._payload_occurred_at(payload)
            if occurred_at is None or occurred_at < start_at or occurred_at > end_at:
                continue

            observation = weather_by_hour.get(hour_start_utc(occurred_at))
            if observation is None or observation.temperature_c is None:
                continue

            temperature = Decimal(observation.temperature_c)
            band = temperature_band(temperature)
            revenue = self._parse_decimal(payload.get("gross_amount"))
            quantity = self._parse_decimal(payload.get("quantity"))
            category_name = self._extract_text(
                payload.get("category_name"),
                fallback=self._unknown_category,
            )
            receipt_key = self._extract_text(
                payload.get("receipt_no"),
                fallback=f"row-{row.id}",
            )

            aggregate[band]["revenue"] += revenue
            aggregate[band]["quantity"] += quantity
            aggregate[band]["count"] += 1
            aggregate[band]["baskets"][receipt_key] += revenue
            aggregate[band]["temperature_sum"] += temperature
            aggregate[band]["temperature_count"] += 1
            aggregate[band]["categories"][category_name] += revenue

        band_order = {"hideg": 0, "enyhe": 1, "meleg": 2, "kanikula": 3}
        insight_rows = [
            self._build_temperature_band_row(band=band, values=values)
            for band, values in aggregate.items()
        ]
        return sorted(
            insight_rows,
            key=lambda row: band_order.get(row.temperature_band, 99),
        )

    def build_condition_insights(
        self,
        *,
        rows: list[ImportRowModel],
        start_at: datetime,
        end_at: datetime,
    ) -> list[DashboardWeatherConditionInsightRow]:
        weather_by_hour = self._weather_by_hour(start_at=start_at, end_at=end_at)
        if not weather_by_hour:
            return []

        aggregate: dict[str, dict[str, Any]] = defaultdict(
            lambda: {
                "revenue": Decimal("0"),
                "quantity": Decimal("0"),
                "count": 0,
                "baskets": defaultdict(Decimal),
                "cloud_sum": Decimal("0"),
                "cloud_count": 0,
                "precipitation_sum": Decimal("0"),
                "categories": defaultdict(Decimal),
            }
        )
        for row in rows:
            payload = row.normalized_payload or {}
            occurred_at = self._payload_occurred_at(payload)
            if occurred_at is None or occurred_at < start_at or occurred_at > end_at:
                continue

            observation = weather_by_hour.get(hour_start_utc(occurred_at))
            if observation is None:
                continue

            condition = weather_condition_band(observation)
            revenue = self._parse_decimal(payload.get("gross_amount"))
            quantity = self._parse_decimal(payload.get("quantity"))
            category_name = self._extract_text(
                payload.get("category_name"),
                fallback=self._unknown_category,
            )
            receipt_key = self._extract_text(
                payload.get("receipt_no"),
                fallback=f"row-{row.id}",
            )

            aggregate[condition]["revenue"] += revenue
            aggregate[condition]["quantity"] += quantity
            aggregate[condition]["count"] += 1
            aggregate[condition]["baskets"][receipt_key] += revenue
            aggregate[condition]["precipitation_sum"] += observation_precipitation(
                observation
            )
            if observation.cloud_cover_percent is not None:
                aggregate[condition]["cloud_sum"] += Decimal(
                    observation.cloud_cover_percent
                )
                aggregate[condition]["cloud_count"] += 1
            aggregate[condition]["categories"][category_name] += revenue

        condition_order = {
            "napos_szaraz": 0,
            "reszben_felhos": 1,
            "borult": 2,
            "csapadekos": 3,
        }
        insight_rows = [
            self._build_condition_row(condition=condition, values=values)
            for condition, values in aggregate.items()
        ]
        return sorted(
            insight_rows,
            key=lambda row: condition_order.get(row.condition_band, 99),
        )

    def list_observations(
        self,
        *,
        start_at: datetime,
        end_at: datetime,
    ) -> list[WeatherObservationHourlyModel]:
        statement = (
            select(WeatherObservationHourlyModel)
            .join(
                WeatherLocationModel,
                WeatherObservationHourlyModel.weather_location_id
                == WeatherLocationModel.id,
            )
            .where(WeatherLocationModel.scope == "shared")
            .where(WeatherLocationModel.name == self._location_name)
            .where(WeatherLocationModel.provider == self._provider)
            .where(WeatherObservationHourlyModel.provider == self._provider)
            .where(WeatherObservationHourlyModel.observed_at >= hour_start_utc(start_at))
            .where(WeatherObservationHourlyModel.observed_at <= hour_start_utc(end_at))
            .order_by(WeatherObservationHourlyModel.observed_at.asc())
        )
        return list(self._session.scalars(statement).all())

    def _weather_by_hour(
        self,
        *,
        start_at: datetime,
        end_at: datetime,
    ) -> dict[datetime, WeatherObservationHourlyModel]:
        return {
            hour_start_utc(observation.observed_at): observation
            for observation in self.list_observations(
                start_at=start_at,
                end_at=end_at,
            )
        }

    def _build_temperature_band_row(
        self,
        *,
        band: str,
        values: dict[str, Any],
    ) -> DashboardTemperatureBandInsightRow:
        baskets = dict(values["baskets"])
        categories = dict(values["categories"])
        basket_count = len(baskets)
        temperature_count = int(values["temperature_count"])
        top_category_name, top_category_revenue = self._top_category(categories)
        revenue = Decimal(values["revenue"])
        return DashboardTemperatureBandInsightRow(
            temperature_band=band,
            revenue=revenue,
            quantity=Decimal(values["quantity"]),
            transaction_count=int(values["count"]),
            basket_count=basket_count,
            average_basket_value=(
                revenue / Decimal(basket_count)
                if basket_count > 0
                else Decimal("0")
            ),
            average_temperature_c=(
                Decimal(values["temperature_sum"]) / Decimal(temperature_count)
                if temperature_count > 0
                else None
            ),
            top_category_name=top_category_name,
            top_category_revenue=top_category_revenue,
            source_layer="weather_enriched_import",
        )

    def _build_condition_row(
        self,
        *,
        condition: str,
        values: dict[str, Any],
    ) -> DashboardWeatherConditionInsightRow:
        baskets = dict(values["baskets"])
        categories = dict(values["categories"])
        basket_count = len(baskets)
        cloud_count = int(values["cloud_count"])
        top_category_name, top_category_revenue = self._top_category(categories)
        revenue = Decimal(values["revenue"])
        return DashboardWeatherConditionInsightRow(
            condition_band=condition,
            revenue=revenue,
            quantity=Decimal(values["quantity"]),
            transaction_count=int(values["count"]),
            basket_count=basket_count,
            average_basket_value=(
                revenue / Decimal(basket_count)
                if basket_count > 0
                else Decimal("0")
            ),
            average_cloud_cover_percent=(
                Decimal(values["cloud_sum"]) / Decimal(cloud_count)
                if cloud_count > 0
                else None
            ),
            precipitation_mm=Decimal(values["precipitation_sum"]),
            top_category_name=top_category_name,
            top_category_revenue=top_category_revenue,
            source_layer="weather_enriched_import",
        )

    def _top_category(
        self,
        categories: dict[str, Decimal],
    ) -> tuple[str, Decimal]:
        if not categories:
            return self._unknown_category, Decimal("0")
        return max(categories.items(), key=lambda item: item[1])

    def _payload_occurred_at(self, payload: dict[str, Any]) -> datetime | None:
        occurred_at = payload.get("occurred_at")
        if isinstance(occurred_at, str):
            try:
                parsed = datetime.fromisoformat(occurred_at)
            except ValueError:
                parsed = None
            if parsed is not None:
                if parsed.tzinfo is None:
                    return parsed.replace(tzinfo=self._time_zone)
                return parsed.astimezone(self._time_zone)

        value = payload.get("date")
        if not isinstance(value, str):
            return None
        try:
            parsed_date = datetime.fromisoformat(value).date()
        except ValueError:
            return None
        return datetime(
            parsed_date.year,
            parsed_date.month,
            parsed_date.day,
            tzinfo=self._time_zone,
        )

    @staticmethod
    def _parse_decimal(value: Any) -> Decimal:
        if value is None:
            return Decimal("0")
        try:
            return Decimal(str(value))
        except (InvalidOperation, ValueError):
            return Decimal("0")

    @staticmethod
    def _extract_text(value: Any, *, fallback: str) -> str:
        if isinstance(value, str) and value.strip():
            return value.strip()
        return fallback


def hour_start_utc(value: datetime) -> datetime:
    aware_value = value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)
    return aware_value.replace(minute=0, second=0, microsecond=0)


def temperature_band(value: Decimal) -> str:
    if value < Decimal("10"):
        return "hideg"
    if value < Decimal("20"):
        return "enyhe"
    if value < Decimal("28"):
        return "meleg"
    return "kanikula"


def weather_condition_band(observation: WeatherObservationHourlyModel) -> str:
    if observation_precipitation(observation) > Decimal("0"):
        return "csapadekos"
    cloud_cover = Decimal(observation.cloud_cover_percent or 0)
    if cloud_cover >= Decimal("70"):
        return "borult"
    if cloud_cover >= Decimal("35"):
        return "reszben_felhos"
    return "napos_szaraz"


def observation_precipitation(
    observation: WeatherObservationHourlyModel,
) -> Decimal:
    values = (
        observation.precipitation_mm,
        observation.rain_mm,
        observation.snowfall_cm,
    )
    return max((Decimal(value or 0) for value in values), default=Decimal("0"))
