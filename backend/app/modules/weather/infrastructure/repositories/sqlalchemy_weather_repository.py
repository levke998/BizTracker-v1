"""SQLAlchemy weather repository."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.master_data.infrastructure.orm.business_unit_model import (
    BusinessUnitModel,
)
from app.modules.master_data.infrastructure.orm.location_model import LocationModel
from app.modules.weather.domain.entities.weather import (
    NewWeatherForecastHourly,
    NewWeatherLocation,
    NewWeatherObservationHourly,
    WeatherForecastHourly,
    WeatherLocation,
    WeatherObservationHourly,
)
from app.modules.weather.infrastructure.orm.weather_model import (
    WeatherForecastHourlyModel,
    WeatherLocationModel,
    WeatherObservationHourlyModel,
)


class SqlAlchemyWeatherRepository:
    """SQLAlchemy persistence adapter for cached weather data."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def business_unit_exists(self, business_unit_id: uuid.UUID) -> bool:
        count = self._session.scalar(
            select(func.count())
            .select_from(BusinessUnitModel)
            .where(BusinessUnitModel.id == business_unit_id)
        )
        return bool(count)

    def location_belongs_to_business_unit(
        self,
        *,
        location_id: uuid.UUID,
        business_unit_id: uuid.UUID,
    ) -> bool:
        count = self._session.scalar(
            select(func.count())
            .select_from(LocationModel)
            .where(LocationModel.id == location_id)
            .where(LocationModel.business_unit_id == business_unit_id)
        )
        return bool(count)

    def get_or_create_location(self, location: NewWeatherLocation) -> WeatherLocation:
        statement = (
            select(WeatherLocationModel)
            .where(WeatherLocationModel.scope == location.scope)
            .where(WeatherLocationModel.name == location.name)
            .where(WeatherLocationModel.provider == location.provider)
        )
        if location.business_unit_id is None:
            statement = statement.where(WeatherLocationModel.business_unit_id.is_(None))
        else:
            statement = statement.where(
                WeatherLocationModel.business_unit_id == location.business_unit_id
            )

        model = self._session.scalar(statement)
        if model is None:
            model = WeatherLocationModel(
                business_unit_id=location.business_unit_id,
                location_id=location.location_id,
                scope=location.scope,
                name=location.name,
                latitude=location.latitude,
                longitude=location.longitude,
                timezone=location.timezone,
                provider=location.provider,
                is_active=location.is_active,
            )
            self._session.add(model)
        else:
            model.location_id = location.location_id
            model.scope = location.scope
            model.latitude = location.latitude
            model.longitude = location.longitude
            model.timezone = location.timezone
            model.is_active = location.is_active

        self._session.commit()
        self._session.refresh(model)
        return self._to_location_entity(model)

    def list_locations(
        self,
        *,
        business_unit_id: uuid.UUID | None = None,
        is_active: bool | None = None,
        limit: int = 100,
    ) -> list[WeatherLocation]:
        statement = select(WeatherLocationModel)
        if business_unit_id is not None:
            statement = statement.where(WeatherLocationModel.business_unit_id == business_unit_id)
        if is_active is not None:
            statement = statement.where(WeatherLocationModel.is_active == is_active)

        statement = statement.order_by(WeatherLocationModel.name.asc()).limit(limit)
        return [
            self._to_location_entity(model)
            for model in self._session.scalars(statement).all()
        ]

    def list_existing_observed_at(
        self,
        *,
        weather_location_id: uuid.UUID,
        provider: str,
        start_at: datetime,
        end_at: datetime,
    ) -> set[datetime]:
        rows = self._session.scalars(
            select(WeatherObservationHourlyModel.observed_at)
            .where(WeatherObservationHourlyModel.weather_location_id == weather_location_id)
            .where(WeatherObservationHourlyModel.provider == provider)
            .where(WeatherObservationHourlyModel.observed_at >= start_at)
            .where(WeatherObservationHourlyModel.observed_at <= end_at)
        ).all()
        return {_as_utc(value) for value in rows}

    def save_observations(
        self,
        observations: list[NewWeatherObservationHourly],
    ) -> tuple[int, int]:
        if not observations:
            return 0, 0

        existing = {
            (model.weather_location_id, _as_utc(model.observed_at), model.provider): model
            for model in self._session.scalars(
                select(WeatherObservationHourlyModel).where(
                    WeatherObservationHourlyModel.weather_location_id.in_(
                        {observation.weather_location_id for observation in observations}
                    )
                )
            ).all()
        }
        created_count = 0
        updated_count = 0
        for observation in observations:
            key = (
                observation.weather_location_id,
                _as_utc(observation.observed_at),
                observation.provider,
            )
            model = existing.get(key)
            values = self._model_values(observation)
            if model is None:
                self._session.add(WeatherObservationHourlyModel(**values))
                created_count += 1
            else:
                for field, value in values.items():
                    setattr(model, field, value)
                model.fetched_at = datetime.now(timezone.utc)
                updated_count += 1

        self._session.commit()
        return created_count, updated_count

    def save_forecasts(
        self,
        forecasts: list[NewWeatherForecastHourly],
    ) -> tuple[int, int]:
        if not forecasts:
            return 0, 0

        existing = {
            (model.weather_location_id, _as_utc(model.forecasted_at), model.provider): model
            for model in self._session.scalars(
                select(WeatherForecastHourlyModel).where(
                    WeatherForecastHourlyModel.weather_location_id.in_(
                        {forecast.weather_location_id for forecast in forecasts}
                    )
                )
            ).all()
        }
        created_count = 0
        updated_count = 0
        for forecast in forecasts:
            key = (
                forecast.weather_location_id,
                _as_utc(forecast.forecasted_at),
                forecast.provider,
            )
            model = existing.get(key)
            values = self._forecast_model_values(forecast)
            if model is None:
                self._session.add(WeatherForecastHourlyModel(**values))
                created_count += 1
            else:
                for field, value in values.items():
                    setattr(model, field, value)
                model.fetched_at = datetime.now(timezone.utc)
                model.updated_at = datetime.now(timezone.utc)
                updated_count += 1

        self._session.commit()
        return created_count, updated_count

    def list_observations(
        self,
        *,
        business_unit_id: uuid.UUID | None = None,
        weather_location_id: uuid.UUID | None = None,
        start_at: datetime | None = None,
        end_at: datetime | None = None,
        limit: int = 500,
    ) -> list[WeatherObservationHourly]:
        statement = select(WeatherObservationHourlyModel)
        if business_unit_id is not None:
            statement = statement.join(
                WeatherLocationModel,
                WeatherLocationModel.id
                == WeatherObservationHourlyModel.weather_location_id,
            ).where(WeatherLocationModel.business_unit_id == business_unit_id)
        if weather_location_id is not None:
            statement = statement.where(
                WeatherObservationHourlyModel.weather_location_id == weather_location_id
            )
        if start_at is not None:
            statement = statement.where(WeatherObservationHourlyModel.observed_at >= start_at)
        if end_at is not None:
            statement = statement.where(WeatherObservationHourlyModel.observed_at <= end_at)

        statement = statement.order_by(WeatherObservationHourlyModel.observed_at.asc()).limit(limit)
        return [
            self._to_observation_entity(model)
            for model in self._session.scalars(statement).all()
        ]

    def list_forecasts(
        self,
        *,
        weather_location_id: uuid.UUID | None = None,
        start_at: datetime | None = None,
        end_at: datetime | None = None,
        limit: int = 500,
    ) -> list[WeatherForecastHourly]:
        statement = select(WeatherForecastHourlyModel)
        if weather_location_id is not None:
            statement = statement.where(
                WeatherForecastHourlyModel.weather_location_id == weather_location_id
            )
        if start_at is not None:
            statement = statement.where(WeatherForecastHourlyModel.forecasted_at >= start_at)
        if end_at is not None:
            statement = statement.where(WeatherForecastHourlyModel.forecasted_at <= end_at)

        statement = statement.order_by(WeatherForecastHourlyModel.forecasted_at.asc()).limit(limit)
        return [
            self._to_forecast_entity(model)
            for model in self._session.scalars(statement).all()
        ]

    @staticmethod
    def _model_values(observation: NewWeatherObservationHourly) -> dict[str, object]:
        return {
            "weather_location_id": observation.weather_location_id,
            "observed_at": observation.observed_at,
            "provider": observation.provider,
            "provider_model": observation.provider_model,
            "weather_code": observation.weather_code,
            "weather_condition": observation.weather_condition,
            "temperature_c": observation.temperature_c,
            "apparent_temperature_c": observation.apparent_temperature_c,
            "relative_humidity_percent": observation.relative_humidity_percent,
            "precipitation_mm": observation.precipitation_mm,
            "rain_mm": observation.rain_mm,
            "snowfall_cm": observation.snowfall_cm,
            "cloud_cover_percent": observation.cloud_cover_percent,
            "wind_speed_kmh": observation.wind_speed_kmh,
            "wind_gust_kmh": observation.wind_gust_kmh,
            "pressure_hpa": observation.pressure_hpa,
            "source_payload": observation.source_payload,
        }

    @staticmethod
    def _forecast_model_values(forecast: NewWeatherForecastHourly) -> dict[str, object]:
        return {
            "weather_location_id": forecast.weather_location_id,
            "forecasted_at": forecast.forecasted_at,
            "provider": forecast.provider,
            "provider_model": forecast.provider_model,
            "forecast_run_at": forecast.forecast_run_at,
            "horizon_hours": forecast.horizon_hours,
            "weather_code": forecast.weather_code,
            "weather_condition": forecast.weather_condition,
            "temperature_c": forecast.temperature_c,
            "apparent_temperature_c": forecast.apparent_temperature_c,
            "relative_humidity_percent": forecast.relative_humidity_percent,
            "precipitation_mm": forecast.precipitation_mm,
            "rain_mm": forecast.rain_mm,
            "snowfall_cm": forecast.snowfall_cm,
            "cloud_cover_percent": forecast.cloud_cover_percent,
            "wind_speed_kmh": forecast.wind_speed_kmh,
            "wind_gust_kmh": forecast.wind_gust_kmh,
            "pressure_hpa": forecast.pressure_hpa,
            "source_payload": forecast.source_payload,
        }

    @staticmethod
    def _to_location_entity(model: WeatherLocationModel) -> WeatherLocation:
        return WeatherLocation(
            id=model.id,
            business_unit_id=model.business_unit_id,
            location_id=model.location_id,
            scope=model.scope,
            name=model.name,
            latitude=model.latitude,
            longitude=model.longitude,
            timezone=model.timezone,
            provider=model.provider,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def _to_observation_entity(
        model: WeatherObservationHourlyModel,
    ) -> WeatherObservationHourly:
        return WeatherObservationHourly(
            id=model.id,
            weather_location_id=model.weather_location_id,
            observed_at=model.observed_at,
            provider=model.provider,
            provider_model=model.provider_model,
            weather_code=model.weather_code,
            weather_condition=model.weather_condition,
            temperature_c=model.temperature_c,
            apparent_temperature_c=model.apparent_temperature_c,
            relative_humidity_percent=model.relative_humidity_percent,
            precipitation_mm=model.precipitation_mm,
            rain_mm=model.rain_mm,
            snowfall_cm=model.snowfall_cm,
            cloud_cover_percent=model.cloud_cover_percent,
            wind_speed_kmh=model.wind_speed_kmh,
            wind_gust_kmh=model.wind_gust_kmh,
            pressure_hpa=model.pressure_hpa,
            source_payload=model.source_payload,
            fetched_at=model.fetched_at,
            created_at=model.created_at,
        )

    @staticmethod
    def _to_forecast_entity(model: WeatherForecastHourlyModel) -> WeatherForecastHourly:
        return WeatherForecastHourly(
            id=model.id,
            weather_location_id=model.weather_location_id,
            forecasted_at=model.forecasted_at,
            provider=model.provider,
            provider_model=model.provider_model,
            forecast_run_at=model.forecast_run_at,
            horizon_hours=model.horizon_hours,
            weather_code=model.weather_code,
            weather_condition=model.weather_condition,
            temperature_c=model.temperature_c,
            apparent_temperature_c=model.apparent_temperature_c,
            relative_humidity_percent=model.relative_humidity_percent,
            precipitation_mm=model.precipitation_mm,
            rain_mm=model.rain_mm,
            snowfall_cm=model.snowfall_cm,
            cloud_cover_percent=model.cloud_cover_percent,
            wind_speed_kmh=model.wind_speed_kmh,
            wind_gust_kmh=model.wind_gust_kmh,
            pressure_hpa=model.pressure_hpa,
            source_payload=model.source_payload,
            fetched_at=model.fetched_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)
