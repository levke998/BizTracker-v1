"""Create inventory_item table in the core schema.

Revision ID: 009_core_inventory_item_base
Revises: 008_core_financial_tx_currency
Create Date: 2026-04-23 19:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "009_core_inventory_item_base"
down_revision = "008_core_financial_tx_currency"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "inventory_item",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("business_unit_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("item_type", sa.String(length=50), nullable=False),
        sa.Column("uom_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "track_stock",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
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
            name="fk_core_inventory_item_business_unit_id_business_unit",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["uom_id"],
            ["core.unit_of_measure.id"],
            name="fk_core_inventory_item_uom_id_unit_of_measure",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_inventory_item"),
        schema="core",
    )
    op.create_index(
        "ix_core_inventory_item_business_unit_id",
        "inventory_item",
        ["business_unit_id"],
        unique=False,
        schema="core",
    )
    op.create_index(
        "ix_core_inventory_item_item_type",
        "inventory_item",
        ["item_type"],
        unique=False,
        schema="core",
    )
    op.create_index(
        "ix_core_inventory_item_name",
        "inventory_item",
        ["name"],
        unique=False,
        schema="core",
    )


def downgrade() -> None:
    op.drop_index(
        "ix_core_inventory_item_name",
        table_name="inventory_item",
        schema="core",
    )
    op.drop_index(
        "ix_core_inventory_item_item_type",
        table_name="inventory_item",
        schema="core",
    )
    op.drop_index(
        "ix_core_inventory_item_business_unit_id",
        table_name="inventory_item",
        schema="core",
    )
    op.drop_table("inventory_item", schema="core")
