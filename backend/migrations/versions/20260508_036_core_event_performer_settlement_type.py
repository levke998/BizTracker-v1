"""Add performer settlement type to events.

Revision ID: 036_core_event_performer_settlement_type
Revises: 035_core_event_cost_line
Create Date: 2026-05-08 00:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "036_core_event_performer_settlement_type"
down_revision = "035_core_event_cost_line"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "event",
        sa.Column(
            "performer_settlement_type",
            sa.String(length=40),
            server_default=sa.text("'hybrid'"),
            nullable=False,
        ),
        schema="core",
    )
    op.create_index(
        "ix_core_event_performer_settlement_type",
        "event",
        ["performer_settlement_type"],
        unique=False,
        schema="core",
    )


def downgrade() -> None:
    op.drop_index(
        "ix_core_event_performer_settlement_type",
        table_name="event",
        schema="core",
    )
    op.drop_column("event", "performer_settlement_type", schema="core")
