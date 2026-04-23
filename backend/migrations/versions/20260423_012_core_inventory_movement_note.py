"""Add note column to inventory_movement.

Revision ID: 012_inventory_movement_note
Revises: 011_core_inventory_movement
Create Date: 2026-04-23 23:35:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "012_inventory_movement_note"
down_revision = "011_core_inventory_movement"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "inventory_movement",
        sa.Column("note", sa.String(length=500), nullable=True),
        schema="core",
    )


def downgrade() -> None:
    op.drop_column("inventory_movement", "note", schema="core")
