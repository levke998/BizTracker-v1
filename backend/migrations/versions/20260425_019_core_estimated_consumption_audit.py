"""Add estimated consumption audit trail.

Revision ID: 019_core_estimated_consumption_audit
Revises: 018_pos_sale_dedupe_key
Create Date: 2026-04-25
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "019_core_estimated_consumption_audit"
down_revision = "018_pos_sale_dedupe_key"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "estimated_consumption_audit",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("business_unit_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("inventory_item_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("recipe_version_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("source_type", sa.String(length=50), nullable=False),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_dedupe_key", sa.String(length=128), nullable=True),
        sa.Column("receipt_no", sa.String(length=100), nullable=True),
        sa.Column("estimation_basis", sa.String(length=50), nullable=False),
        sa.Column("quantity", sa.Numeric(14, 3), nullable=False),
        sa.Column("uom_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("quantity_before", sa.Numeric(14, 3), nullable=False),
        sa.Column("quantity_after", sa.Numeric(14, 3), nullable=False),
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
            name="fk_core_estimated_consumption_business_unit_id_business_unit",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["product_id"],
            ["core.product.id"],
            name="fk_core_estimated_consumption_product_id_product",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["inventory_item_id"],
            ["core.inventory_item.id"],
            name="fk_core_estimated_consumption_inventory_item_id_inventory_item",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["recipe_version_id"],
            ["core.recipe_version.id"],
            name="fk_core_estimated_consumption_recipe_version_id_recipe_version",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["uom_id"],
            ["core.unit_of_measure.id"],
            name="fk_core_estimated_consumption_uom_id_unit_of_measure",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_estimated_consumption_audit"),
        sa.UniqueConstraint(
            "source_type",
            "source_id",
            "product_id",
            "inventory_item_id",
            name="uq_core_estimated_consumption_source_product_item",
        ),
        schema="core",
    )
    op.create_index(
        "ix_core_estimated_consumption_business_unit_id",
        "estimated_consumption_audit",
        ["business_unit_id"],
        unique=False,
        schema="core",
    )
    op.create_index(
        "ix_core_estimated_consumption_inventory_item_id",
        "estimated_consumption_audit",
        ["inventory_item_id"],
        unique=False,
        schema="core",
    )
    op.create_index(
        "ix_core_estimated_consumption_product_id",
        "estimated_consumption_audit",
        ["product_id"],
        unique=False,
        schema="core",
    )
    op.create_index(
        "ix_core_estimated_consumption_source_ref",
        "estimated_consumption_audit",
        ["source_type", "source_id"],
        unique=False,
        schema="core",
    )


def downgrade() -> None:
    op.drop_index(
        "ix_core_estimated_consumption_source_ref",
        table_name="estimated_consumption_audit",
        schema="core",
    )
    op.drop_index(
        "ix_core_estimated_consumption_product_id",
        table_name="estimated_consumption_audit",
        schema="core",
    )
    op.drop_index(
        "ix_core_estimated_consumption_inventory_item_id",
        table_name="estimated_consumption_audit",
        schema="core",
    )
    op.drop_index(
        "ix_core_estimated_consumption_business_unit_id",
        table_name="estimated_consumption_audit",
        schema="core",
    )
    op.drop_table("estimated_consumption_audit", schema="core")
