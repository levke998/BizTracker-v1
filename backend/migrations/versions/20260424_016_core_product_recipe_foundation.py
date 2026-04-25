"""Add product price fields and production recipe foundation.

Revision ID: 016_product_recipe_base
Revises: 015_inventory_movement_source_ref
Create Date: 2026-04-24
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "016_product_recipe_base"
down_revision = "015_inventory_movement_source_ref"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "product",
        sa.Column("sale_price_gross", sa.Numeric(12, 2), nullable=True),
        schema="core",
    )
    op.add_column(
        "product",
        sa.Column("default_unit_cost", sa.Numeric(12, 2), nullable=True),
        schema="core",
    )
    op.add_column(
        "product",
        sa.Column(
            "currency",
            sa.String(length=3),
            nullable=False,
            server_default=sa.text("'HUF'"),
        ),
        schema="core",
    )

    op.create_table(
        "recipe",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
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
            ["product_id"],
            ["core.product.id"],
            name="fk_core_recipe_product_id_product",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_recipe"),
        sa.UniqueConstraint("product_id", "name", name="uq_core_recipe_product_name"),
        schema="core",
    )
    op.create_index(
        "ix_core_recipe_product_id",
        "recipe",
        ["product_id"],
        unique=False,
        schema="core",
    )

    op.create_table(
        "recipe_version",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("recipe_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version_no", sa.Integer(), nullable=False),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "valid_from",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("yield_quantity", sa.Numeric(12, 3), nullable=False),
        sa.Column("yield_uom_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("notes", sa.String(length=500), nullable=True),
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
            ["recipe_id"],
            ["core.recipe.id"],
            name="fk_core_recipe_version_recipe_id_recipe",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["yield_uom_id"],
            ["core.unit_of_measure.id"],
            name="fk_core_recipe_version_yield_uom_id_unit_of_measure",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_recipe_version"),
        sa.UniqueConstraint(
            "recipe_id",
            "version_no",
            name="uq_core_recipe_version_recipe_version_no",
        ),
        schema="core",
    )
    op.create_index(
        "ix_core_recipe_version_recipe_id",
        "recipe_version",
        ["recipe_id"],
        unique=False,
        schema="core",
    )

    op.create_table(
        "recipe_ingredient",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("recipe_version_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("inventory_item_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("quantity", sa.Numeric(12, 3), nullable=False),
        sa.Column("uom_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(
            ["recipe_version_id"],
            ["core.recipe_version.id"],
            name="fk_core_recipe_ingredient_recipe_version_id_recipe_version",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["inventory_item_id"],
            ["core.inventory_item.id"],
            name="fk_core_recipe_ingredient_inventory_item_id_inventory_item",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["uom_id"],
            ["core.unit_of_measure.id"],
            name="fk_core_recipe_ingredient_uom_id_unit_of_measure",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_recipe_ingredient"),
        sa.UniqueConstraint(
            "recipe_version_id",
            "inventory_item_id",
            name="uq_core_recipe_ingredient_version_item",
        ),
        schema="core",
    )
    op.create_index(
        "ix_core_recipe_ingredient_recipe_version_id",
        "recipe_ingredient",
        ["recipe_version_id"],
        unique=False,
        schema="core",
    )
    op.create_index(
        "ix_core_recipe_ingredient_inventory_item_id",
        "recipe_ingredient",
        ["inventory_item_id"],
        unique=False,
        schema="core",
    )


def downgrade() -> None:
    op.drop_index(
        "ix_core_recipe_ingredient_inventory_item_id",
        table_name="recipe_ingredient",
        schema="core",
    )
    op.drop_index(
        "ix_core_recipe_ingredient_recipe_version_id",
        table_name="recipe_ingredient",
        schema="core",
    )
    op.drop_table("recipe_ingredient", schema="core")

    op.drop_index(
        "ix_core_recipe_version_recipe_id",
        table_name="recipe_version",
        schema="core",
    )
    op.drop_table("recipe_version", schema="core")

    op.drop_index("ix_core_recipe_product_id", table_name="recipe", schema="core")
    op.drop_table("recipe", schema="core")

    op.drop_column("product", "currency", schema="core")
    op.drop_column("product", "default_unit_cost", schema="core")
    op.drop_column("product", "sale_price_gross", schema="core")
