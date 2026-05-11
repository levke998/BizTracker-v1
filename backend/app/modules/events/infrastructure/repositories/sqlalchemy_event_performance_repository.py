"""SQLAlchemy event performance read-model repository."""

from __future__ import annotations

import uuid
from collections import Counter, defaultdict
from datetime import UTC, datetime, timedelta
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.events.domain.entities.event_performance import (
    EventPerformance,
    EventPerformanceCategoryRow,
    EventPerformanceProductRow,
    EventWeatherSummary,
)
from app.modules.events.infrastructure.orm.event_model import EventModel
from app.modules.events.infrastructure.orm.event_ticket_actual_model import (
    EventTicketActualModel,
)
from app.modules.imports.infrastructure.orm.import_batch_model import ImportBatchModel
from app.modules.imports.infrastructure.orm.import_row_model import ImportRowModel
from app.modules.weather.application.commands.sync_shared_weather import (
    SHARED_WEATHER_LOCATION_NAME,
    SHARED_WEATHER_PROVIDER,
)
from app.modules.weather.infrastructure.orm.weather_model import (
    WeatherLocationModel,
    WeatherObservationHourlyModel,
)

APP_TIME_ZONE = ZoneInfo("Europe/Budapest")
DEFAULT_EVENT_DURATION = timedelta(hours=8)
MONEY_QUANT = Decimal("0.01")
PERCENT_QUANT = Decimal("0.01")
UNKNOWN_CATEGORY = "Kategória nélkül"
UNKNOWN_PRODUCT = "Ismeretlen termék"


class SqlAlchemyEventPerformanceRepository:
    """Build event performance from stored event windows and POS/weather rows."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_event_id(self, event_id: uuid.UUID) -> EventPerformance | None:
        event = self._session.get(EventModel, event_id)
        if event is None:
            return None
        return self._build_event_performance(event)

    def list_many(
        self,
        *,
        business_unit_id: uuid.UUID | None = None,
        status: str | None = None,
        is_active: bool | None = None,
        starts_from: datetime | None = None,
        starts_to: datetime | None = None,
        limit: int = 50,
    ) -> list[EventPerformance]:
        statement = select(EventModel)

        if business_unit_id is not None:
            statement = statement.where(EventModel.business_unit_id == business_unit_id)
        if status is not None:
            statement = statement.where(EventModel.status == status)
        if is_active is not None:
            statement = statement.where(EventModel.is_active == is_active)
        if starts_from is not None:
            statement = statement.where(EventModel.starts_at >= starts_from)
        if starts_to is not None:
            statement = statement.where(EventModel.starts_at <= starts_to)

        statement = statement.order_by(EventModel.starts_at.desc()).limit(limit)
        return [
            self._build_event_performance(event)
            for event in self._session.scalars(statement).all()
        ]

    def _build_event_performance(self, event: EventModel) -> EventPerformance:
        starts_at = self._as_app_time(event.starts_at)
        ends_at = self._as_app_time(event.ends_at) if event.ends_at else starts_at + DEFAULT_EVENT_DURATION
        rows = self._list_event_pos_rows(
            business_unit_id=event.business_unit_id,
            starts_at=starts_at,
            ends_at=ends_at,
        )
        source_row_count = 0
        receipt_keys: set[str] = set()
        ticket_revenue = Decimal("0")
        bar_revenue = Decimal("0")
        ticket_quantity = Decimal("0")
        bar_quantity = Decimal("0")
        category_totals: dict[str, dict[str, Decimal | int]] = defaultdict(
            lambda: {"gross_amount": Decimal("0"), "quantity": Decimal("0"), "row_count": 0}
        )
        product_totals: dict[tuple[str, str], dict[str, Decimal | int]] = defaultdict(
            lambda: {"gross_amount": Decimal("0"), "quantity": Decimal("0"), "row_count": 0}
        )

        for row in rows:
            payload = row.normalized_payload or {}
            source_row_count += 1
            gross_amount = self._parse_decimal(payload.get("gross_amount"))
            quantity = self._parse_decimal(payload.get("quantity"))
            category_name = self._extract_text(payload.get("category_name"), fallback=UNKNOWN_CATEGORY)
            product_name = self._extract_text(payload.get("product_name"), fallback=UNKNOWN_PRODUCT)
            receipt_no = self._extract_optional_text(payload.get("receipt_no")) or str(row.id)
            receipt_keys.add(receipt_no)

            category_totals[category_name]["gross_amount"] += gross_amount
            category_totals[category_name]["quantity"] += quantity
            category_totals[category_name]["row_count"] += 1
            product_totals[(product_name, category_name)]["gross_amount"] += gross_amount
            product_totals[(product_name, category_name)]["quantity"] += quantity
            product_totals[(product_name, category_name)]["row_count"] += 1

            bar_revenue += gross_amount
            bar_quantity += quantity

        ticket_actual = self._get_ticket_actual(event.id)
        platform_fee_gross = Decimal("0")
        ticket_revenue_source = "not_recorded"
        if ticket_actual is not None:
            ticket_revenue = Decimal(ticket_actual.gross_revenue)
            ticket_quantity = Decimal(ticket_actual.sold_quantity)
            platform_fee_gross = Decimal(ticket_actual.platform_fee_gross)
            ticket_revenue_source = "ticket_actual"

        performer_share_percent = Decimal(event.performer_share_percent)
        performer_share_amount = self._money(ticket_revenue * performer_share_percent / Decimal("100"))
        retained_ticket_revenue = self._money(ticket_revenue - performer_share_amount)
        own_revenue = self._money(retained_ticket_revenue + bar_revenue)
        operating_cost_gross = self._money(
            Decimal(event.performer_fixed_fee)
            + Decimal(event.event_cost_amount)
            + platform_fee_gross
        )
        event_profit_lite = self._money(own_revenue - operating_cost_gross)
        total_revenue = self._money(ticket_revenue + bar_revenue)

        return EventPerformance(
            event_id=event.id,
            business_unit_id=event.business_unit_id,
            starts_at=starts_at,
            ends_at=ends_at,
            source_row_count=source_row_count,
            receipt_count=len(receipt_keys),
            ticket_revenue_gross=self._money(ticket_revenue),
            bar_revenue_gross=self._money(bar_revenue),
            total_revenue_gross=total_revenue,
            ticket_quantity=ticket_quantity,
            bar_quantity=bar_quantity,
            performer_share_percent=performer_share_percent,
            performer_share_amount=performer_share_amount,
            retained_ticket_revenue=retained_ticket_revenue,
            platform_fee_gross=self._money(platform_fee_gross),
            own_revenue=own_revenue,
            operating_cost_gross=operating_cost_gross,
            event_profit_lite=event_profit_lite,
            event_profit_margin_percent=self._ratio_percent(event_profit_lite, own_revenue),
            operating_cost_ratio_percent=self._ratio_percent(operating_cost_gross, own_revenue),
            ticket_revenue_share_percent=self._ratio_percent(ticket_revenue, total_revenue),
            bar_revenue_share_percent=self._ratio_percent(bar_revenue, total_revenue),
            profit_status=self._profit_status(event_profit_lite, own_revenue),
            ticket_revenue_source=ticket_revenue_source,
            settlement_status=self._settlement_status(ticket_revenue_source),
            categories=tuple(self._category_rows(category_totals)),
            top_products=tuple(self._product_rows(product_totals, limit=10)),
            weather=self._build_weather_summary(starts_at=starts_at, ends_at=ends_at),
        )

    def _list_event_pos_rows(
        self,
        *,
        business_unit_id: uuid.UUID,
        starts_at: datetime,
        ends_at: datetime,
    ) -> list[ImportRowModel]:
        statement = (
            select(ImportRowModel)
            .join(ImportBatchModel, ImportBatchModel.id == ImportRowModel.batch_id)
            .where(ImportBatchModel.business_unit_id == business_unit_id)
            .where(ImportBatchModel.import_type.in_(("pos_sales", "gourmand_pos_sales", "flow_pos_sales")))
            .where(ImportRowModel.parse_status == "parsed")
            .order_by(ImportRowModel.row_number.asc())
        )

        matched_rows: list[ImportRowModel] = []
        for row in self._session.scalars(statement).all():
            occurred_at = self._payload_occurred_at(row.normalized_payload or {})
            if occurred_at is not None and starts_at <= occurred_at <= ends_at:
                matched_rows.append(row)
        return matched_rows

    def _get_ticket_actual(self, event_id: uuid.UUID) -> EventTicketActualModel | None:
        return self._session.scalar(
            select(EventTicketActualModel).where(EventTicketActualModel.event_id == event_id)
        )

    @staticmethod
    def _settlement_status(ticket_revenue_source: str) -> str:
        if ticket_revenue_source == "ticket_actual":
            return "actual_ticket_settlement"
        return "ticket_actual_missing"

    @staticmethod
    def _profit_status(profit: Decimal, own_revenue: Decimal) -> str:
        if own_revenue <= 0:
            return "no_revenue"
        if profit > 0:
            return "profitable"
        if profit < 0:
            return "loss"
        return "break_even"

    @staticmethod
    def _ratio_percent(numerator: Decimal, denominator: Decimal) -> Decimal | None:
        if denominator <= 0:
            return None
        return (numerator * Decimal("100") / denominator).quantize(
            PERCENT_QUANT,
            rounding=ROUND_HALF_UP,
        )

    def _build_weather_summary(self, *, starts_at: datetime, ends_at: datetime) -> EventWeatherSummary:
        observations = self._list_shared_weather_observations(starts_at=starts_at, ends_at=ends_at)
        if not observations:
            return EventWeatherSummary(
                observation_count=0,
                dominant_condition=None,
                average_temperature_c=None,
                total_precipitation_mm=Decimal("0"),
                average_cloud_cover_percent=None,
                average_wind_speed_kmh=None,
            )

        conditions = Counter(observation.weather_condition for observation in observations)
        dominant_condition = conditions.most_common(1)[0][0]
        return EventWeatherSummary(
            observation_count=len(observations),
            dominant_condition=dominant_condition,
            average_temperature_c=self._average_decimal(
                observation.temperature_c for observation in observations
            ),
            total_precipitation_mm=sum(
                (self._observation_precipitation(observation) for observation in observations),
                Decimal("0"),
            ),
            average_cloud_cover_percent=self._average_decimal(
                observation.cloud_cover_percent for observation in observations
            ),
            average_wind_speed_kmh=self._average_decimal(
                observation.wind_speed_kmh for observation in observations
            ),
        )

    def _list_shared_weather_observations(
        self,
        *,
        starts_at: datetime,
        ends_at: datetime,
    ) -> list[WeatherObservationHourlyModel]:
        period_start = self._hour_start_utc(starts_at)
        period_end = self._hour_start_utc(ends_at)
        statement = (
            select(WeatherObservationHourlyModel)
            .join(WeatherLocationModel, WeatherObservationHourlyModel.weather_location_id == WeatherLocationModel.id)
            .where(WeatherLocationModel.scope == "shared")
            .where(WeatherLocationModel.name == SHARED_WEATHER_LOCATION_NAME)
            .where(WeatherLocationModel.provider == SHARED_WEATHER_PROVIDER)
            .where(WeatherObservationHourlyModel.provider == SHARED_WEATHER_PROVIDER)
            .where(WeatherObservationHourlyModel.observed_at >= period_start)
            .where(WeatherObservationHourlyModel.observed_at <= period_end)
            .order_by(WeatherObservationHourlyModel.observed_at.asc())
        )
        return list(self._session.scalars(statement).all())

    @staticmethod
    def _category_rows(
        aggregate: dict[str, dict[str, Decimal | int]],
    ) -> list[EventPerformanceCategoryRow]:
        rows = [
            EventPerformanceCategoryRow(
                category_name=category_name,
                gross_amount=Decimal(values["gross_amount"]),
                quantity=Decimal(values["quantity"]),
                row_count=int(values["row_count"]),
            )
            for category_name, values in aggregate.items()
        ]
        return sorted(rows, key=lambda row: row.gross_amount, reverse=True)

    @staticmethod
    def _product_rows(
        aggregate: dict[tuple[str, str], dict[str, Decimal | int]],
        *,
        limit: int,
    ) -> list[EventPerformanceProductRow]:
        rows = [
            EventPerformanceProductRow(
                product_name=product_name,
                category_name=category_name,
                gross_amount=Decimal(values["gross_amount"]),
                quantity=Decimal(values["quantity"]),
                row_count=int(values["row_count"]),
            )
            for (product_name, category_name), values in aggregate.items()
        ]
        return sorted(rows, key=lambda row: row.gross_amount, reverse=True)[:limit]

    @staticmethod
    def _observation_precipitation(observation: WeatherObservationHourlyModel) -> Decimal:
        values = (
            observation.precipitation_mm,
            observation.rain_mm,
            observation.snowfall_cm,
        )
        return max((Decimal(value or 0) for value in values), default=Decimal("0"))

    @staticmethod
    def _average_decimal(values: Any) -> Decimal | None:
        decimals = [Decimal(value) for value in values if value is not None]
        if not decimals:
            return None
        return sum(decimals, Decimal("0")) / Decimal(len(decimals))

    @staticmethod
    def _payload_occurred_at(payload: dict[str, Any]) -> datetime | None:
        occurred_at = payload.get("occurred_at")
        if isinstance(occurred_at, str):
            try:
                parsed = datetime.fromisoformat(occurred_at)
            except ValueError:
                parsed = None
            if parsed is not None:
                return SqlAlchemyEventPerformanceRepository._as_app_time(parsed)

        payload_date = payload.get("date")
        if not isinstance(payload_date, str):
            return None
        try:
            parsed_date = datetime.fromisoformat(payload_date)
        except ValueError:
            return None
        return SqlAlchemyEventPerformanceRepository._as_app_time(parsed_date)

    @staticmethod
    def _as_app_time(value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=APP_TIME_ZONE)
        return value.astimezone(APP_TIME_ZONE)

    @staticmethod
    def _hour_start_utc(value: datetime) -> datetime:
        aware_value = value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)
        return aware_value.replace(minute=0, second=0, microsecond=0)

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

    @staticmethod
    def _extract_optional_text(value: Any) -> str | None:
        if isinstance(value, str) and value.strip():
            return value.strip()
        return None

    @staticmethod
    def _money(value: Decimal) -> Decimal:
        return value.quantize(MONEY_QUANT)
