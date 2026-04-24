"""Add source reference fields to inventory movements.

Revision ID: 015_inventory_movement_source_ref
Revises: 014_core_supplier_invoice_base
Create Date: 2026-04-24
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "015_inventory_movement_source_ref"
down_revision = "014_core_supplier_invoice_base"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "inventory_movement",
        sa.Column("source_type", sa.String(length=100), nullable=True),
        schema="core",
    )
    op.add_column(
        "inventory_movement",
        sa.Column("source_id", sa.Uuid(as_uuid=True), nullable=True),
        schema="core",
    )
    op.create_index(
        "ix_core_inventory_movement_source_ref",
        "inventory_movement",
        ["source_type", "source_id"],
        unique=False,
        schema="core",
    )
    op.create_unique_constraint(
        "uq_core_inventory_movement_source_ref",
        "inventory_movement",
        ["source_type", "source_id"],
        schema="core",
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_core_inventory_movement_source_ref",
        "inventory_movement",
        schema="core",
        type_="unique",
    )
    op.drop_index(
        "ix_core_inventory_movement_source_ref",
        table_name="inventory_movement",
        schema="core",
    )
    op.drop_column("inventory_movement", "source_id", schema="core")
    op.drop_column("inventory_movement", "source_type", schema="core")
