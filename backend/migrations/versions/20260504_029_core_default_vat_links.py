"""Add default VAT links to catalog and inventory items.

Revision ID: 029_core_default_vat_links
Revises: 028_core_event_ticket_actual
Create Date: 2026-05-04 15:45:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "029_core_default_vat_links"
down_revision: Union[str, None] = "028_core_event_ticket_actual"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "product",
        sa.Column("default_vat_rate_id", sa.Uuid(as_uuid=True), nullable=True),
        schema="core",
    )
    op.create_foreign_key(
        "fk_core_product_default_vat_rate_id",
        "product",
        "vat_rate",
        ["default_vat_rate_id"],
        ["id"],
        source_schema="core",
        referent_schema="core",
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_core_product_default_vat_rate_id",
        "product",
        ["default_vat_rate_id"],
        unique=False,
        schema="core",
    )

    op.add_column(
        "inventory_item",
        sa.Column("default_vat_rate_id", sa.Uuid(as_uuid=True), nullable=True),
        schema="core",
    )
    op.create_foreign_key(
        "fk_core_inventory_item_default_vat_rate_id",
        "inventory_item",
        "vat_rate",
        ["default_vat_rate_id"],
        ["id"],
        source_schema="core",
        referent_schema="core",
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_core_inventory_item_default_vat_rate_id",
        "inventory_item",
        ["default_vat_rate_id"],
        unique=False,
        schema="core",
    )


def downgrade() -> None:
    op.drop_index(
        "ix_core_inventory_item_default_vat_rate_id",
        table_name="inventory_item",
        schema="core",
    )
    op.drop_constraint(
        "fk_core_inventory_item_default_vat_rate_id",
        "inventory_item",
        schema="core",
        type_="foreignkey",
    )
    op.drop_column("inventory_item", "default_vat_rate_id", schema="core")

    op.drop_index(
        "ix_core_product_default_vat_rate_id",
        table_name="product",
        schema="core",
    )
    op.drop_constraint(
        "fk_core_product_default_vat_rate_id",
        "product",
        schema="core",
        type_="foreignkey",
    )
    op.drop_column("product", "default_vat_rate_id", schema="core")
