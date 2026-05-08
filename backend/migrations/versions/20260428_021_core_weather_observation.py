"""Create weather cache tables.

Revision ID: 021_core_weather_observation
Revises: 020_core_event_base
Create Date: 2026-04-28
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "021_core_weather_observation"
down_revision = "020_core_event_base"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "weather_location",
        sa.Column("business_unit_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("location_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("latitude", sa.Numeric(9, 6), nullable=False),
        sa.Column("longitude", sa.Numeric(9, 6), nullable=False),
        sa.Column(
            "timezone",
            sa.String(length=80),
            nullable=False,
            server_default=sa.text("'Europe/Budapest'"),
        ),
        sa.Column(
            "provider",
            sa.String(length=50),
            nullable=False,
            server_default=sa.text("'open_meteo'"),
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
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
        sa.ForeignKeyConstraint(
            ["business_unit_id"],
            ["core.business_unit.id"],
            name="fk_core_weather_location_business_unit_id_business_unit",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["location_id"],
            ["core.location.id"],
            name="fk_core_weather_location_location_id_location",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_weather_location"),
        sa.UniqueConstraint(
            "business_unit_id",
            "name",
            "provider",
            name="uq_core_weather_location_business_unit_name_provider",
        ),
        schema="core",
    )
    op.create_index(
        "ix_core_weather_location_business_unit_id",
        "weather_location",
        ["business_unit_id"],
        unique=False,
        schema="core",
    )
    op.create_index(
        "ix_core_weather_location_location_id",
        "weather_location",
        ["location_id"],
        unique=False,
        schema="core",
    )
    op.create_index(
        "ix_core_weather_location_is_active",
        "weather_location",
        ["is_active"],
        unique=False,
        schema="core",
    )

    op.create_table(
        "weather_observation_hourly",
        sa.Column("weather_location_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("provider_model", sa.String(length=100), nullable=True),
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
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.ForeignKeyConstraint(
            ["weather_location_id"],
            ["core.weather_location.id"],
            name="fk_core_weather_obs_location_id_weather_location",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_weather_observation_hourly"),
        sa.UniqueConstraint(
            "weather_location_id",
            "observed_at",
            "provider",
            name="uq_core_weather_observation_location_time_provider",
        ),
        schema="core",
    )
    op.create_index(
        "ix_core_weather_observation_weather_location_id",
        "weather_observation_hourly",
        ["weather_location_id"],
        unique=False,
        schema="core",
    )
    op.create_index(
        "ix_core_weather_observation_observed_at",
        "weather_observation_hourly",
        ["observed_at"],
        unique=False,
        schema="core",
    )
    op.create_index(
        "ix_core_weather_observation_condition",
        "weather_observation_hourly",
        ["weather_condition"],
        unique=False,
        schema="core",
    )


def downgrade() -> None:
    op.drop_index(
        "ix_core_weather_observation_condition",
        table_name="weather_observation_hourly",
        schema="core",
    )
    op.drop_index(
        "ix_core_weather_observation_observed_at",
        table_name="weather_observation_hourly",
        schema="core",
    )
    op.drop_index(
        "ix_core_weather_observation_weather_location_id",
        table_name="weather_observation_hourly",
        schema="core",
    )
    op.drop_table("weather_observation_hourly", schema="core")
    op.drop_index("ix_core_weather_location_is_active", table_name="weather_location", schema="core")
    op.drop_index("ix_core_weather_location_location_id", table_name="weather_location", schema="core")
    op.drop_index(
        "ix_core_weather_location_business_unit_id",
        table_name="weather_location",
        schema="core",
    )
    op.drop_table("weather_location", schema="core")
