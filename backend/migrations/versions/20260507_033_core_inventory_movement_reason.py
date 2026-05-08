"""Add inventory movement reason code.

Revision ID: 033_core_inventory_movement_reason
Revises: 032_core_inventory_cost_source
Create Date: 2026-05-07 00:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "033_core_inventory_movement_reason"
down_revision = "032_core_inventory_cost_source"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "inventory_movement",
        sa.Column("reason_code", sa.String(length=50), nullable=True),
        schema="core",
    )
    op.create_index(
        "ix_core_inventory_movement_reason_code",
        "inventory_movement",
        ["reason_code"],
        unique=False,
        schema="core",
    )


def downgrade() -> None:
    op.drop_index(
        "ix_core_inventory_movement_reason_code",
        table_name="inventory_movement",
        schema="core",
    )
    op.drop_column("inventory_movement", "reason_code", schema="core")
