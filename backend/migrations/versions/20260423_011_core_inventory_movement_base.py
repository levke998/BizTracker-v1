"""Create inventory_movement table in the core schema.

Revision ID: 011_core_inventory_movement
Revises: 010_inventory_item_name_uq
Create Date: 2026-04-23 23:15:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "011_core_inventory_movement"
down_revision = "010_inventory_item_name_uq"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "inventory_movement",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("business_unit_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("inventory_item_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("movement_type", sa.String(length=50), nullable=False),
        sa.Column("quantity", sa.Numeric(precision=12, scale=3), nullable=False),
        sa.Column("uom_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("unit_cost", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(
            ["business_unit_id"],
            ["core.business_unit.id"],
            name="fk_core_inventory_movement_business_unit_id_business_unit",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["inventory_item_id"],
            ["core.inventory_item.id"],
            name="fk_core_inventory_movement_inventory_item_id_inventory_item",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["uom_id"],
            ["core.unit_of_measure.id"],
            name="fk_core_inventory_movement_uom_id_unit_of_measure",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_inventory_movement"),
        schema="core",
    )
    op.create_index(
        "ix_core_inventory_movement_business_unit_id",
        "inventory_movement",
        ["business_unit_id"],
        unique=False,
        schema="core",
    )
    op.create_index(
        "ix_core_inventory_movement_inventory_item_id",
        "inventory_movement",
        ["inventory_item_id"],
        unique=False,
        schema="core",
    )
    op.create_index(
        "ix_core_inventory_movement_occurred_at",
        "inventory_movement",
        ["occurred_at"],
        unique=False,
        schema="core",
    )


def downgrade() -> None:
    op.drop_index(
        "ix_core_inventory_movement_occurred_at",
        table_name="inventory_movement",
        schema="core",
    )
    op.drop_index(
        "ix_core_inventory_movement_inventory_item_id",
        table_name="inventory_movement",
        schema="core",
    )
    op.drop_index(
        "ix_core_inventory_movement_business_unit_id",
        table_name="inventory_movement",
        schema="core",
    )
    op.drop_table("inventory_movement", schema="core")
