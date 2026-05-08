"""Create supplier item alias table.

Revision ID: 031_core_supplier_item_alias
Revises: 030_core_supplier_invoice_line_vat
Create Date: 2026-05-04 17:20:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "031_core_supplier_item_alias"
down_revision: Union[str, None] = "030_core_supplier_invoice_line_vat"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "supplier_item_alias",
        sa.Column("business_unit_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("supplier_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("inventory_item_id", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column("source_item_name", sa.String(length=255), nullable=False),
        sa.Column("source_item_key", sa.String(length=255), nullable=False),
        sa.Column("internal_display_name", sa.String(length=255), nullable=True),
        sa.Column(
            "status",
            sa.String(length=50),
            nullable=False,
            server_default=sa.text("'review_required'"),
        ),
        sa.Column(
            "mapping_confidence",
            sa.String(length=50),
            nullable=False,
            server_default=sa.text("'manual_review'"),
        ),
        sa.Column(
            "occurrence_count",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "first_seen_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "last_seen_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "id",
            sa.Uuid(as_uuid=True),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["business_unit_id"],
            ["core.business_unit.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["supplier_id"],
            ["core.supplier.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["inventory_item_id"],
            ["core.inventory_item.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "business_unit_id",
            "supplier_id",
            "source_item_key",
            name="uq_core_supplier_item_alias_source",
        ),
        schema="core",
    )
    op.create_index(
        "ix_core_supplier_item_alias_business_unit_id",
        "supplier_item_alias",
        ["business_unit_id"],
        unique=False,
        schema="core",
    )
    op.create_index(
        "ix_core_supplier_item_alias_supplier_id",
        "supplier_item_alias",
        ["supplier_id"],
        unique=False,
        schema="core",
    )
    op.create_index(
        "ix_core_supplier_item_alias_inventory_item_id",
        "supplier_item_alias",
        ["inventory_item_id"],
        unique=False,
        schema="core",
    )
    op.create_index(
        "ix_core_supplier_item_alias_status",
        "supplier_item_alias",
        ["status"],
        unique=False,
        schema="core",
    )


def downgrade() -> None:
    op.drop_index(
        "ix_core_supplier_item_alias_status",
        table_name="supplier_item_alias",
        schema="core",
    )
    op.drop_index(
        "ix_core_supplier_item_alias_inventory_item_id",
        table_name="supplier_item_alias",
        schema="core",
    )
    op.drop_index(
        "ix_core_supplier_item_alias_supplier_id",
        table_name="supplier_item_alias",
        schema="core",
    )
    op.drop_index(
        "ix_core_supplier_item_alias_business_unit_id",
        table_name="supplier_item_alias",
        schema="core",
    )
    op.drop_table("supplier_item_alias", schema="core")
