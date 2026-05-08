"""Track POS sale price freshness on products.

Revision ID: 025_core_product_sale_price_observation
Revises: 024_core_pos_product_alias
Create Date: 2026-05-04
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "025_core_product_sale_price_observation"
down_revision = "024_core_pos_product_alias"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "product",
        sa.Column("sale_price_last_seen_at", sa.DateTime(timezone=True), nullable=True),
        schema="core",
    )
    op.add_column(
        "product",
        sa.Column("sale_price_source", sa.String(length=50), nullable=True),
        schema="core",
    )
    op.create_index(
        "ix_core_product_sale_price_last_seen_at",
        "product",
        ["sale_price_last_seen_at"],
        unique=False,
        schema="core",
    )


def downgrade() -> None:
    op.drop_index(
        "ix_core_product_sale_price_last_seen_at",
        table_name="product",
        schema="core",
    )
    op.drop_column("product", "sale_price_source", schema="core")
    op.drop_column("product", "sale_price_last_seen_at", schema="core")
