"""SQLAlchemy import-batch weather recommendation repository."""

from __future__ import annotations

import uuid
from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.modules.imports.infrastructure.orm.import_batch_model import ImportBatchModel
from app.modules.imports.infrastructure.orm.import_row_model import ImportRowModel
from app.modules.master_data.infrastructure.orm.business_unit_model import (
    BusinessUnitModel,
)
from app.modules.weather.application.queries.import_batch_weather import (
    ImportBatchWeatherContext,
)
from app.modules.weather.infrastructure.orm.weather_model import (
    WeatherLocationModel,
    WeatherObservationHourlyModel,
)

APP_TIME_ZONE = ZoneInfo("Europe/Budapest")


class SqlAlchemyImportWeatherRepository:
    """Read import batch and weather cache state for recommendations."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_import_batch_context(
        self,
        batch_id: uuid.UUID,
    ) -> ImportBatchWeatherContext | None:
        statement: Select[tuple[ImportBatchModel, BusinessUnitModel]] = (
            select(ImportBatchModel, BusinessUnitModel)
            .join(BusinessUnitModel, BusinessUnitModel.id == ImportBatchModel.business_unit_id)
            .where(ImportBatchModel.id == batch_id)
        )
        result = self._session.execute(statement).one_or_none()
        if result is None:
            return None

        batch, business_unit = result
        sale_times = self._sale_times(batch_id=batch_id)
        return ImportBatchWeatherContext(
            batch_id=batch.id,
            business_unit_id=batch.business_unit_id,
            business_unit_code=business_unit.code,
            business_unit_name=business_unit.name,
            import_type=batch.import_type,
            status=batch.status,
            parsed_rows=batch.parsed_rows,
            first_sale_at=min(sale_times) if sale_times else None,
            last_sale_at=max(sale_times) if sale_times else None,
        )

    def count_cached_weather_hours(
        self,
        *,
        location_name: str,
        provider_name: str,
        start_at: datetime,
        end_at: datetime,
    ) -> int:
        count = self._session.scalar(
            select(func.count())
            .select_from(WeatherObservationHourlyModel)
            .join(
                WeatherLocationModel,
                WeatherLocationModel.id == WeatherObservationHourlyModel.weather_location_id,
            )
            .where(WeatherLocationModel.scope == "shared")
            .where(WeatherLocationModel.name == location_name)
            .where(WeatherLocationModel.provider == provider_name)
            .where(WeatherObservationHourlyModel.provider == provider_name)
            .where(WeatherObservationHourlyModel.observed_at >= start_at)
            .where(WeatherObservationHourlyModel.observed_at <= end_at)
        )
        return int(count or 0)

    def _sale_times(self, *, batch_id: uuid.UUID) -> list[datetime]:
        rows = self._session.scalars(
            select(ImportRowModel)
            .where(ImportRowModel.batch_id == batch_id)
            .where(ImportRowModel.parse_status == "parsed")
            .order_by(ImportRowModel.row_number.asc())
        ).all()
        sale_times: list[datetime] = []
        for row in rows:
            payload = row.normalized_payload or {}
            occurred_at = _parse_occurred_at(payload.get("occurred_at"))
            if occurred_at is not None:
                sale_times.append(occurred_at)
        return sale_times


def _parse_occurred_at(value: object) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=APP_TIME_ZONE)
    return parsed.astimezone(APP_TIME_ZONE)
