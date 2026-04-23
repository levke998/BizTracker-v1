"""Create foundation master data tables in the core schema.

Revision ID: 003_core_master_data_foundation
Revises: 002_auth_identity_base
Create Date: 2026-04-22 19:05:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "003_core_master_data_foundation"
down_revision = "002_auth_identity_base"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "business_unit",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("type", sa.String(length=50), nullable=False),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
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
        sa.PrimaryKeyConstraint("id", name="pk_business_unit"),
        sa.UniqueConstraint("code", name="uq_core_business_unit_code"),
        schema="core",
    )
    op.create_index(
        "ix_core_business_unit_code",
        "business_unit",
        ["code"],
        unique=False,
        schema="core",
    )

    op.create_table(
        "location",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("business_unit_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("kind", sa.String(length=50), nullable=False),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
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
            name="fk_core_location_business_unit_id_business_unit",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_location"),
        sa.UniqueConstraint(
            "business_unit_id",
            "name",
            name="uq_core_location_business_unit_name",
        ),
        schema="core",
    )
    op.create_index(
        "ix_core_location_business_unit_id",
        "location",
        ["business_unit_id"],
        unique=False,
        schema="core",
    )

    op.create_table(
        "unit_of_measure",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("code", sa.String(length=20), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("symbol", sa.String(length=20), nullable=True),
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
        sa.PrimaryKeyConstraint("id", name="pk_unit_of_measure"),
        sa.UniqueConstraint("code", name="uq_core_unit_of_measure_code"),
        schema="core",
    )
    op.create_index(
        "ix_core_unit_of_measure_code",
        "unit_of_measure",
        ["code"],
        unique=False,
        schema="core",
    )


def downgrade() -> None:
    op.drop_index(
        "ix_core_unit_of_measure_code",
        table_name="unit_of_measure",
        schema="core",
    )
    op.drop_table("unit_of_measure", schema="core")

    op.drop_index(
        "ix_core_location_business_unit_id",
        table_name="location",
        schema="core",
    )
    op.drop_table("location", schema="core")

    op.drop_index(
        "ix_core_business_unit_code",
        table_name="business_unit",
        schema="core",
    )
    op.drop_table("business_unit", schema="core")
