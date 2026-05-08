"""Create weather forecast cache table.

Revision ID: 023_core_weather_forecast_cache
Revises: 022_core_shared_weather_location
Create Date: 2026-05-01
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "023_core_weather_forecast_cache"
down_revision = "022_core_shared_weather_location"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "weather_forecast_hourly",
        sa.Column("weather_location_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("forecasted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("provider_model", sa.String(length=100), nullable=True),
        sa.Column("forecast_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("horizon_hours", sa.Integer(), nullable=True),
        sa.Column("weather_code", sa.Integer(), nullable=True),
        sa.Column(
            "weather_condition",
            sa.String(length=50),
            nullable=False,
            server_default=sa.text("'ismeretlen'"),
        ),
        sa.Column("temperature_c", sa.Numeric(6, 2), nullable=True),
        sa.Column("apparent_temperature_c", sa.Numeric(6, 2), nullable=True),
        sa.Column("relative_humidity_percent", sa.Numeric(5, 2), nullable=True),
        sa.Column("precipitation_mm", sa.Numeric(8, 3), nullable=True),
        sa.Column("rain_mm", sa.Numeric(8, 3), nullable=True),
        sa.Column("snowfall_cm", sa.Numeric(8, 3), nullable=True),
        sa.Column("cloud_cover_percent", sa.Numeric(5, 2), nullable=True),
        sa.Column("wind_speed_kmh", sa.Numeric(6, 2), nullable=True),
        sa.Column("wind_gust_kmh", sa.Numeric(6, 2), nullable=True),
        sa.Column("pressure_hpa", sa.Numeric(7, 2), nullable=True),
        sa.Column("source_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "fetched_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.ForeignKeyConstraint(
            ["weather_location_id"],
            ["core.weather_location.id"],
            name="fk_core_weather_forecast_location_id_weather_location",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_weather_forecast_hourly"),
        sa.UniqueConstraint(
            "weather_location_id",
            "forecasted_at",
            "provider",
            name="uq_core_weather_forecast_location_time_provider",
        ),
        schema="core",
    )
    op.create_index(
        "ix_core_weather_forecast_weather_location_id",
        "weather_forecast_hourly",
        ["weather_location_id"],
        unique=False,
        schema="core",
    )
    op.create_index(
        "ix_core_weather_forecast_forecasted_at",
        "weather_forecast_hourly",
        ["forecasted_at"],
        unique=False,
        schema="core",
    )
    op.create_index(
        "ix_core_weather_forecast_condition",
        "weather_forecast_hourly",
        ["weather_condition"],
        unique=False,
        schema="core",
    )


def downgrade() -> None:
    op.drop_index(
        "ix_core_weather_forecast_condition",
        table_name="weather_forecast_hourly",
        schema="core",
    )
    op.drop_index(
        "ix_core_weather_forecast_forecasted_at",
        table_name="weather_forecast_hourly",
        schema="core",
    )
    op.drop_index(
        "ix_core_weather_forecast_weather_location_id",
        table_name="weather_forecast_hourly",
        schema="core",
    )
    op.drop_table("weather_forecast_hourly", schema="core")
