"""Add unique constraint to inventory item name per business unit.

Revision ID: 010_inventory_item_name_uq
Revises: 009_core_inventory_item_base
Create Date: 2026-04-23 21:00:00
"""

from __future__ import annotations

from alembic import op

# revision identifiers, used by Alembic.
revision = "010_inventory_item_name_uq"
down_revision = "009_core_inventory_item_base"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_core_inventory_item_business_unit_name",
        "inventory_item",
        ["business_unit_id", "name"],
        schema="core",
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_core_inventory_item_business_unit_name",
        "inventory_item",
        schema="core",
        type_="unique",
    )
