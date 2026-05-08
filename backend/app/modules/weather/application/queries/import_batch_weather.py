"""Import batch weather recommendation query."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Protocol

from app.modules.weather.application.commands.backfill_weather import (
    _expected_observed_hours,
)
from app.modules.weather.application.commands.sync_shared_weather import (
    SHARED_WEATHER_LATITUDE,
    SHARED_WEATHER_LOCATION_NAME,
    SHARED_WEATHER_LONGITUDE,
    SHARED_WEATHER_PROVIDER,
    SHARED_WEATHER_TIMEZONE,
)

SUPPORTED_POS_IMPORT_TYPES = {"gourmand_pos_sales", "flow_pos_sales", "pos_sales"}
DEFAULT_WEATHER_LOCATIONS_BY_IMPORT_TYPE = {
    "gourmand_pos_sales": {
        "name": SHARED_WEATHER_LOCATION_NAME,
        "latitude": SHARED_WEATHER_LATITUDE,
        "longitude": SHARED_WEATHER_LONGITUDE,
        "timezone_name": SHARED_WEATHER_TIMEZONE,
    },
    "flow_pos_sales": {
        "name": SHARED_WEATHER_LOCATION_NAME,
        "latitude": SHARED_WEATHER_LATITUDE,
        "longitude": SHARED_WEATHER_LONGITUDE,
        "timezone_name": SHARED_WEATHER_TIMEZONE,
    },
    "pos_sales": {
        "name": SHARED_WEATHER_LOCATION_NAME,
        "latitude": SHARED_WEATHER_LATITUDE,
        "longitude": SHARED_WEATHER_LONGITUDE,
        "timezone_name": SHARED_WEATHER_TIMEZONE,
    },
}


@dataclass(frozen=True, slots=True)
class ImportBatchWeatherContext:
    """Raw import batch weather context from persistence."""

    batch_id: uuid.UUID
    business_unit_id: uuid.UUID
    business_unit_code: str
    business_unit_name: str
    import_type: str
    status: str
    parsed_rows: int
    first_sale_at: datetime | None
    last_sale_at: datetime | None


@dataclass(frozen=True, slots=True)
class ImportBatchWeatherRecommendation:
    """Weather backfill recommendation for one import batch."""

    batch_id: uuid.UUID
    business_unit_id: uuid.UUID
    business_unit_code: str
    business_unit_name: str
    import_type: str
    status: str
    parsed_rows: int
    can_backfill: bool
    reason: str | None
    first_sale_at: datetime | None
    last_sale_at: datetime | None
    start_date: date | None
    end_date: date | None
    timezone_name: str
    suggested_location_name: str
    latitude: Decimal
    longitude: Decimal
    provider_name: str
    requested_hours: int
    cached_hours: int
    missing_hours: int


class ImportBatchWeatherRepository(Protocol):
    """Read boundary for import-batch-based weather preparation."""

    def get_import_batch_context(
        self,
        batch_id: uuid.UUID,
    ) -> ImportBatchWeatherContext | None:
        """Return import batch context and parsed POS time range."""

    def count_cached_weather_hours(
        self,
        *,
        location_name: str,
        provider_name: str,
        start_at: datetime,
        end_at: datetime,
    ) -> int:
        """Return existing cached weather hours for the suggested lookup point."""


@dataclass(slots=True)
class GetImportBatchWeatherRecommendationQuery:
    """Build a weather backfill recommendation from parsed POS import data."""

    repository: ImportBatchWeatherRepository

    def execute(self, *, batch_id: uuid.UUID) -> ImportBatchWeatherRecommendation:
        context = self.repository.get_import_batch_context(batch_id)
        if context is None:
            raise ImportBatchWeatherNotFoundError(f"Import batch {batch_id} was not found.")

        defaults = DEFAULT_WEATHER_LOCATIONS_BY_IMPORT_TYPE.get(
            context.import_type,
            DEFAULT_WEATHER_LOCATIONS_BY_IMPORT_TYPE["pos_sales"],
        )
        timezone_name = str(defaults["timezone_name"])
        start_date = context.first_sale_at.date() if context.first_sale_at else None
        end_date = context.last_sale_at.date() if context.last_sale_at else None

        can_backfill = True
        reason: str | None = None
        requested_hours = 0
        cached_hours = 0
        missing_hours = 0

        if context.import_type not in SUPPORTED_POS_IMPORT_TYPES:
            can_backfill = False
            reason = "Ehhez az import típushoz nem kapcsolunk időjárás-előkészítést."
        elif context.status != "parsed":
            can_backfill = False
            reason = "Az időjárás előkészítéséhez előbb fel kell dolgozni az importot."
        elif context.first_sale_at is None or context.last_sale_at is None:
            can_backfill = False
            reason = "Az import nem tartalmaz időponttal rendelkező eladási sort."

        if start_date is not None and end_date is not None:
            expected_hours = _expected_observed_hours(
                start_date=start_date,
                end_date=end_date,
                timezone_name=timezone_name,
            )
            requested_hours = len(expected_hours)
            if expected_hours:
                cached_hours = self.repository.count_cached_weather_hours(
                    location_name=str(defaults["name"]),
                    provider_name=SHARED_WEATHER_PROVIDER,
                    start_at=min(expected_hours),
                    end_at=max(expected_hours),
                )
                missing_hours = max(requested_hours - cached_hours, 0)

        return ImportBatchWeatherRecommendation(
            batch_id=context.batch_id,
            business_unit_id=context.business_unit_id,
            business_unit_code=context.business_unit_code,
            business_unit_name=context.business_unit_name,
            import_type=context.import_type,
            status=context.status,
            parsed_rows=context.parsed_rows,
            can_backfill=can_backfill,
            reason=reason,
            first_sale_at=context.first_sale_at,
            last_sale_at=context.last_sale_at,
            start_date=start_date,
            end_date=end_date,
            timezone_name=timezone_name,
            suggested_location_name=str(defaults["name"]),
            latitude=defaults["latitude"],  # type: ignore[arg-type]
            longitude=defaults["longitude"],  # type: ignore[arg-type]
            provider_name=SHARED_WEATHER_PROVIDER,
            requested_hours=requested_hours,
            cached_hours=cached_hours,
            missing_hours=missing_hours,
        )


class ImportBatchWeatherNotFoundError(Exception):
    """Raised when an import batch cannot be found."""
