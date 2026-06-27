"""Create event cost line table.

Revision ID: 035_core_event_cost_line
Revises: 034_core_inventory_variance_threshold
Create Date: 2026-05-08 00:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "035_core_event_cost_line"
down_revision = "034_core_inventory_variance_threshold"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "event_cost_line",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("event_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("category", sa.String(length=80), nullable=False),
        sa.Column("description", sa.String(length=240), nullable=False),
        sa.Column(
            "amount_gross",
            sa.Numeric(14, 2),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column(
            "source_type",
            sa.String(length=40),
            server_default=sa.text("'manual'"),
            nullable=False,
        ),
        sa.Column("source_reference", sa.String(length=180), nullable=True),
        sa.Column("incurred_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["event_id"], ["core.event.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        schema="core",
    )
    op.create_index(
        "ix_core_event_cost_line_event_id",
        "event_cost_line",
        ["event_id"],
        unique=False,
        schema="core",
    )
    op.create_index(
        "ix_core_event_cost_line_category",
        "event_cost_line",
        ["category"],
        unique=False,
        schema="core",
    )


def downgrade() -> None:
    op.drop_index(
        "ix_core_event_cost_line_category",
        table_name="event_cost_line",
        schema="core",
    )
    op.drop_index(
        "ix_core_event_cost_line_event_id",
        table_name="event_cost_line",
        schema="core",
    )
    op.drop_table("event_cost_line", schema="core")
