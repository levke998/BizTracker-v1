"""Weather ORM models."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
import uuid

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class WeatherLocationModel(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Stores one weather lookup point."""

    __tablename__ = "weather_location"
    __table_args__ = (
        sa.Index("ix_core_weather_location_scope", "scope"),
        sa.Index("ix_core_weather_location_business_unit_id", "business_unit_id"),
        sa.Index("ix_core_weather_location_location_id", "location_id"),
        sa.Index("ix_core_weather_location_is_active", "is_active"),
        sa.Index(
            "uq_core_weather_location_shared_name_provider",
            "name",
            "provider",
            unique=True,
            postgresql_where=sa.text("scope = 'shared'"),
        ),
        sa.Index(
            "uq_core_weather_location_unit_name_provider",
            "business_unit_id",
            "name",
            "provider",
            unique=True,
            postgresql_where=sa.text("scope = 'business_unit'"),
        ),
        {"schema": "core"},
    )

    business_unit_id: Mapped[uuid.UUID | None] = mapped_column(
        sa.Uuid(as_uuid=True),
        sa.ForeignKey("core.business_unit.id", ondelete="RESTRICT"),
        nullable=True,
    )
    location_id: Mapped[uuid.UUID | None] = mapped_column(
        sa.Uuid(as_uuid=True),
        sa.ForeignKey("core.location.id", ondelete="SET NULL"),
        nullable=True,
    )
    scope: Mapped[str] = mapped_column(
        sa.String(30),
        nullable=False,
        server_default=sa.text("'business_unit'"),
    )
    name: Mapped[str] = mapped_column(sa.String(150), nullable=False)
    latitude: Mapped[Decimal] = mapped_column(sa.Numeric(9, 6), nullable=False)
    longitude: Mapped[Decimal] = mapped_column(sa.Numeric(9, 6), nullable=False)
    timezone: Mapped[str] = mapped_column(
        sa.String(80),
        nullable=False,
        server_default=sa.text("'Europe/Budapest'"),
    )
    provider: Mapped[str] = mapped_column(
        sa.String(50),
        nullable=False,
        server_default=sa.text("'open_meteo'"),
    )
    is_active: Mapped[bool] = mapped_column(
        sa.Boolean,
        nullable=False,
        server_default=sa.text("true"),
    )


class WeatherObservationHourlyModel(UUIDPrimaryKeyMixin, Base):
    """Stores one hourly weather observation."""

    __tablename__ = "weather_observation_hourly"
    __table_args__ = (
        sa.UniqueConstraint(
            "weather_location_id",
            "observed_at",
            "provider",
            name="uq_core_weather_observation_location_time_provider",
        ),
        sa.Index(
            "ix_core_weather_observation_weather_location_id",
            "weather_location_id",
        ),
        sa.Index("ix_core_weather_observation_observed_at", "observed_at"),
        sa.Index("ix_core_weather_observation_condition", "weather_condition"),
        {"schema": "core"},
    )

    weather_location_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid(as_uuid=True),
        sa.ForeignKey("core.weather_location.id", ondelete="CASCADE"),
        nullable=False,
    )
    observed_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False)
    provider: Mapped[str] = mapped_column(sa.String(50), nullable=False)
    provider_model: Mapped[str | None] = mapped_column(sa.String(100), nullable=True)
    weather_code: Mapped[int | None] = mapped_column(sa.Integer, nullable=True)
    weather_condition: Mapped[str] = mapped_column(
        sa.String(50),
        nullable=False,
        server_default=sa.text("'ismeretlen'"),
    )
    temperature_c: Mapped[Decimal | None] = mapped_column(sa.Numeric(6, 2), nullable=True)
    apparent_temperature_c: Mapped[Decimal | None] = mapped_column(
        sa.Numeric(6, 2),
        nullable=True,
    )
    relative_humidity_percent: Mapped[Decimal | None] = mapped_column(
        sa.Numeric(5, 2),
        nullable=True,
    )
    precipitation_mm: Mapped[Decimal | None] = mapped_column(sa.Numeric(8, 3), nullable=True)
    rain_mm: Mapped[Decimal | None] = mapped_column(sa.Numeric(8, 3), nullable=True)
    snowfall_cm: Mapped[Decimal | None] = mapped_column(sa.Numeric(8, 3), nullable=True)
    cloud_cover_percent: Mapped[Decimal | None] = mapped_column(sa.Numeric(5, 2), nullable=True)
    wind_speed_kmh: Mapped[Decimal | None] = mapped_column(sa.Numeric(6, 2), nullable=True)
    wind_gust_kmh: Mapped[Decimal | None] = mapped_column(sa.Numeric(6, 2), nullable=True)
    pressure_hpa: Mapped[Decimal | None] = mapped_column(sa.Numeric(7, 2), nullable=True)
    source_payload: Mapped[dict[str, object] | None] = mapped_column(JSONB, nullable=True)
    fetched_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
    )
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
    )


class WeatherForecastHourlyModel(UUIDPrimaryKeyMixin, Base):
    """Stores one hourly weather forecast snapshot for planning."""

    __tablename__ = "weather_forecast_hourly"
    __table_args__ = (
        sa.UniqueConstraint(
            "weather_location_id",
            "forecasted_at",
            "provider",
            name="uq_core_weather_forecast_location_time_provider",
        ),
        sa.Index(
            "ix_core_weather_forecast_weather_location_id",
            "weather_location_id",
        ),
        sa.Index("ix_core_weather_forecast_forecasted_at", "forecasted_at"),
        sa.Index("ix_core_weather_forecast_condition", "weather_condition"),
        {"schema": "core"},
    )

    weather_location_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid(as_uuid=True),
        sa.ForeignKey("core.weather_location.id", ondelete="CASCADE"),
        nullable=False,
    )
    forecasted_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False)
    provider: Mapped[str] = mapped_column(sa.String(50), nullable=False)
    provider_model: Mapped[str | None] = mapped_column(sa.String(100), nullable=True)
    forecast_run_at: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=True,
    )
    horizon_hours: Mapped[int | None] = mapped_column(sa.Integer, nullable=True)
    weather_code: Mapped[int | None] = mapped_column(sa.Integer, nullable=True)
    weather_condition: Mapped[str] = mapped_column(
        sa.String(50),
        nullable=False,
        server_default=sa.text("'ismeretlen'"),
    )
    temperature_c: Mapped[Decimal | None] = mapped_column(sa.Numeric(6, 2), nullable=True)
    apparent_temperature_c: Mapped[Decimal | None] = mapped_column(
        sa.Numeric(6, 2),
        nullable=True,
    )
    relative_humidity_percent: Mapped[Decimal | None] = mapped_column(
        sa.Numeric(5, 2),
        nullable=True,
    )
    precipitation_mm: Mapped[Decimal | None] = mapped_column(sa.Numeric(8, 3), nullable=True)
    rain_mm: Mapped[Decimal | None] = mapped_column(sa.Numeric(8, 3), nullable=True)
    snowfall_cm: Mapped[Decimal | None] = mapped_column(sa.Numeric(8, 3), nullable=True)
    cloud_cover_percent: Mapped[Decimal | None] = mapped_column(sa.Numeric(5, 2), nullable=True)
    wind_speed_kmh: Mapped[Decimal | None] = mapped_column(sa.Numeric(6, 2), nullable=True)
    wind_gust_kmh: Mapped[Decimal | None] = mapped_column(sa.Numeric(6, 2), nullable=True)
    pressure_hpa: Mapped[Decimal | None] = mapped_column(sa.Numeric(7, 2), nullable=True)
    source_payload: Mapped[dict[str, object] | None] = mapped_column(JSONB, nullable=True)
    fetched_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
    )
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
    )
