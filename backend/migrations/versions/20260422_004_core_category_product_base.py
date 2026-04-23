"""Create category and product tables in the core schema.

Revision ID: 004_core_category_product_base
Revises: 003_core_master_data_foundation
Create Date: 2026-04-22 19:20:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "004_core_category_product_base"
down_revision = "003_core_master_data_foundation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "category",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("business_unit_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("parent_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("name", sa.String(length=150), nullable=False),
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
            name="fk_core_category_business_unit_id_business_unit",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["parent_id"],
            ["core.category.id"],
            name="fk_core_category_parent_id_category",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_category"),
        schema="core",
    )
    op.create_index(
        "ix_core_category_business_unit_id",
        "category",
        ["business_unit_id"],
        unique=False,
        schema="core",
    )
    op.create_index(
        "ix_core_category_parent_id",
        "category",
        ["parent_id"],
        unique=False,
        schema="core",
    )
    op.create_index(
        "ix_core_category_business_unit_parent_name",
        "category",
        ["business_unit_id", "parent_id", "name"],
        unique=False,
        schema="core",
    )

    op.create_table(
        "product",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("business_unit_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("category_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("sku", sa.String(length=64), nullable=True),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("product_type", sa.String(length=50), nullable=False),
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
            name="fk_core_product_business_unit_id_business_unit",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["category_id"],
            ["core.category.id"],
            name="fk_core_product_category_id_category",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_product"),
        schema="core",
    )
    op.create_index(
        "ix_core_product_business_unit_id",
        "product",
        ["business_unit_id"],
        unique=False,
        schema="core",
    )
    op.create_index(
        "ix_core_product_category_id",
        "product",
        ["category_id"],
        unique=False,
        schema="core",
    )
    op.create_index(
        "ix_core_product_sku",
        "product",
        ["sku"],
        unique=False,
        schema="core",
    )
    op.create_index(
        "ix_core_product_business_unit_name",
        "product",
        ["business_unit_id", "name"],
        unique=False,
        schema="core",
    )


def downgrade() -> None:
    op.drop_index(
        "ix_core_product_business_unit_name",
        table_name="product",
        schema="core",
    )
    op.drop_index(
        "ix_core_product_sku",
        table_name="product",
        schema="core",
    )
    op.drop_index(
        "ix_core_product_category_id",
        table_name="product",
        schema="core",
    )
    op.drop_index(
        "ix_core_product_business_unit_id",
        table_name="product",
        schema="core",
    )
    op.drop_table("product", schema="core")

    op.drop_index(
        "ix_core_category_business_unit_parent_name",
        table_name="category",
        schema="core",
    )
    op.drop_index(
        "ix_core_category_parent_id",
        table_name="category",
        schema="core",
    )
    op.drop_index(
        "ix_core_category_business_unit_id",
        table_name="category",
        schema="core",
    )
    op.drop_table("category", schema="core")
