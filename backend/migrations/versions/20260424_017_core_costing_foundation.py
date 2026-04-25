"""Add product sales unit and inventory costing fields.

Revision ID: 017_core_costing_foundation
Revises: 016_product_recipe_base
Create Date: 2026-04-24
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "017_core_costing_foundation"
down_revision = "016_product_recipe_base"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "inventory_item",
        sa.Column("default_unit_cost", sa.Numeric(14, 4), nullable=True),
        schema="core",
    )
    op.add_column(
        "inventory_item",
        sa.Column("estimated_stock_quantity", sa.Numeric(14, 3), nullable=True),
        schema="core",
    )
    op.add_column(
        "product",
        sa.Column("sales_uom_id", sa.Uuid(as_uuid=True), nullable=True),
        schema="core",
    )
    op.create_foreign_key(
        "fk_core_product_sales_uom_id_unit_of_measure",
        "product",
        "unit_of_measure",
        ["sales_uom_id"],
        ["id"],
        source_schema="core",
        referent_schema="core",
        ondelete="RESTRICT",
    )
    op.create_index(
        "ix_core_product_sales_uom_id",
        "product",
        ["sales_uom_id"],
        unique=False,
        schema="core",
    )


def downgrade() -> None:
    op.drop_index(
        "ix_core_product_sales_uom_id",
        table_name="product",
        schema="core",
    )
    op.drop_constraint(
        "fk_core_product_sales_uom_id_unit_of_measure",
        "product",
        schema="core",
        type_="foreignkey",
    )
    op.drop_column("product", "sales_uom_id", schema="core")
    op.drop_column("inventory_item", "estimated_stock_quantity", schema="core")
    op.drop_column("inventory_item", "default_unit_cost", schema="core")
