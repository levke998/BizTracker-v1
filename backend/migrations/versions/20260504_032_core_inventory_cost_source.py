"""Add inventory item default cost source metadata.

Revision ID: 032_core_inventory_cost_source
Revises: 031_core_supplier_item_alias
Create Date: 2026-05-04 18:00:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "032_core_inventory_cost_source"
down_revision: Union[str, None] = "031_core_supplier_item_alias"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "inventory_item",
        sa.Column("default_unit_cost_last_seen_at", sa.DateTime(timezone=True), nullable=True),
        schema="core",
    )
    op.add_column(
        "inventory_item",
        sa.Column("default_unit_cost_source_type", sa.String(length=80), nullable=True),
        schema="core",
    )
    op.add_column(
        "inventory_item",
        sa.Column("default_unit_cost_source_id", sa.Uuid(as_uuid=True), nullable=True),
        schema="core",
    )
    op.create_index(
        "ix_core_inventory_item_default_unit_cost_seen_at",
        "inventory_item",
        ["default_unit_cost_last_seen_at"],
        unique=False,
        schema="core",
    )


def downgrade() -> None:
    op.drop_index(
        "ix_core_inventory_item_default_unit_cost_seen_at",
        table_name="inventory_item",
        schema="core",
    )
    op.drop_column("inventory_item", "default_unit_cost_source_id", schema="core")
    op.drop_column("inventory_item", "default_unit_cost_source_type", schema="core")
    op.drop_column("inventory_item", "default_unit_cost_last_seen_at", schema="core")
