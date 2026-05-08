"""Create event planning table.

Revision ID: 020_core_event_base
Revises: 019_core_estimated_consumption_audit
Create Date: 2026-04-27
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "020_core_event_base"
down_revision = "019_core_estimated_consumption_audit"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "event",
        sa.Column("business_unit_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("location_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("title", sa.String(length=180), nullable=False),
        sa.Column(
            "status",
            sa.String(length=30),
            nullable=False,
            server_default=sa.text("'planned'"),
        ),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("performer_name", sa.String(length=180), nullable=True),
        sa.Column("expected_attendance", sa.Integer(), nullable=True),
        sa.Column(
            "ticket_revenue_gross",
            sa.Numeric(14, 2),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "bar_revenue_gross",
            sa.Numeric(14, 2),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "performer_share_percent",
            sa.Numeric(5, 2),
            nullable=False,
            server_default=sa.text("80"),
        ),
        sa.Column(
            "performer_fixed_fee",
            sa.Numeric(14, 2),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "event_cost_amount",
            sa.Numeric(14, 2),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column("notes", sa.Text(), nullable=True),
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
            name="fk_core_event_business_unit_id_business_unit",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["location_id"],
            ["core.location.id"],
            name="fk_core_event_location_id_location",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_event"),
        schema="core",
    )
    op.create_index(
        "ix_core_event_business_unit_id",
        "event",
        ["business_unit_id"],
        unique=False,
        schema="core",
    )
    op.create_index(
        "ix_core_event_location_id",
        "event",
        ["location_id"],
        unique=False,
        schema="core",
    )
    op.create_index(
        "ix_core_event_starts_at",
        "event",
        ["starts_at"],
        unique=False,
        schema="core",
    )
    op.create_index(
        "ix_core_event_status",
        "event",
        ["status"],
        unique=False,
        schema="core",
    )


def downgrade() -> None:
    op.drop_index("ix_core_event_status", table_name="event", schema="core")
    op.drop_index("ix_core_event_starts_at", table_name="event", schema="core")
    op.drop_index("ix_core_event_location_id", table_name="event", schema="core")
    op.drop_index("ix_core_event_business_unit_id", table_name="event", schema="core")
    op.drop_table("event", schema="core")
