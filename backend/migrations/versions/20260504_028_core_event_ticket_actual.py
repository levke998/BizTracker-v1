"""Create event ticket actual table.

Revision ID: 028_core_event_ticket_actual
Revises: 027_core_vat_rate
Create Date: 2026-05-04 15:25:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "028_core_event_ticket_actual"
down_revision: Union[str, None] = "027_core_vat_rate"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "event_ticket_actual",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("event_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("source_name", sa.String(length=120), nullable=True),
        sa.Column("source_reference", sa.String(length=180), nullable=True),
        sa.Column("sold_quantity", sa.Numeric(12, 3), server_default=sa.text("0"), nullable=False),
        sa.Column("gross_revenue", sa.Numeric(14, 2), server_default=sa.text("0"), nullable=False),
        sa.Column("net_revenue", sa.Numeric(14, 2), nullable=True),
        sa.Column("vat_amount", sa.Numeric(14, 2), nullable=True),
        sa.Column("vat_rate_id", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column(
            "platform_fee_gross",
            sa.Numeric(14, 2),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column("reported_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.ForeignKeyConstraint(["vat_rate_id"], ["core.vat_rate.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("event_id", name="uq_core_event_ticket_actual_event_id"),
        schema="core",
    )
    op.create_index(
        "ix_core_event_ticket_actual_event_id",
        "event_ticket_actual",
        ["event_id"],
        unique=False,
        schema="core",
    )


def downgrade() -> None:
    op.drop_index(
        "ix_core_event_ticket_actual_event_id",
        table_name="event_ticket_actual",
        schema="core",
    )
    op.drop_table("event_ticket_actual", schema="core")
