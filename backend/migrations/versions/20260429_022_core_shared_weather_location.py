"""Allow shared weather locations.

Revision ID: 022_core_shared_weather_location
Revises: 021_core_weather_observation
Create Date: 2026-04-29
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "022_core_shared_weather_location"
down_revision = "021_core_weather_observation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "weather_location",
        sa.Column(
            "scope",
            sa.String(length=30),
            nullable=False,
            server_default=sa.text("'business_unit'"),
        ),
        schema="core",
    )
    op.drop_constraint(
        "uq_core_weather_location_business_unit_name_provider",
        "weather_location",
        schema="core",
        type_="unique",
    )
    op.alter_column(
        "weather_location",
        "business_unit_id",
        existing_type=sa.Uuid(as_uuid=True),
        nullable=True,
        schema="core",
    )
    op.create_index(
        "ix_core_weather_location_scope",
        "weather_location",
        ["scope"],
        unique=False,
        schema="core",
    )
    op.create_index(
        "uq_core_weather_location_shared_name_provider",
        "weather_location",
        ["name", "provider"],
        unique=True,
        schema="core",
        postgresql_where=sa.text("scope = 'shared'"),
    )
    op.create_index(
        "uq_core_weather_location_unit_name_provider",
        "weather_location",
        ["business_unit_id", "name", "provider"],
        unique=True,
        schema="core",
        postgresql_where=sa.text("scope = 'business_unit'"),
    )


def downgrade() -> None:
    op.execute("DELETE FROM core.weather_location WHERE scope = 'shared'")
    op.drop_index(
        "uq_core_weather_location_unit_name_provider",
        table_name="weather_location",
        schema="core",
    )
    op.drop_index(
        "uq_core_weather_location_shared_name_provider",
        table_name="weather_location",
        schema="core",
    )
    op.drop_index(
        "ix_core_weather_location_scope",
        table_name="weather_location",
        schema="core",
    )
    op.alter_column(
        "weather_location",
        "business_unit_id",
        existing_type=sa.Uuid(as_uuid=True),
        nullable=False,
        schema="core",
    )
    op.create_unique_constraint(
        "uq_core_weather_location_business_unit_name_provider",
        "weather_location",
        ["business_unit_id", "name", "provider"],
        schema="core",
    )
    op.drop_column("weather_location", "scope", schema="core")
