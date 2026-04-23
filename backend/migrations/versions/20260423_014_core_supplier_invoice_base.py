"""Create supplier invoice tables in the core schema.

Revision ID: 014_core_supplier_invoice_base
Revises: 013_core_supplier_base
Create Date: 2026-04-23
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "014_core_supplier_invoice_base"
down_revision = "013_core_supplier_base"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "supplier_invoice",
        sa.Column("business_unit_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("supplier_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("invoice_number", sa.String(length=120), nullable=False),
        sa.Column("invoice_date", sa.Date(), nullable=False),
        sa.Column(
            "currency",
            sa.String(length=3),
            nullable=False,
            server_default=sa.text("'HUF'"),
        ),
        sa.Column("gross_total", sa.Numeric(14, 2), nullable=False),
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
            server_default=sa.text("timezone('utc', now())"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("timezone('utc', now())"),
        ),
        sa.ForeignKeyConstraint(
            ["business_unit_id"],
            ["core.business_unit.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["supplier_id"],
            ["core.supplier.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "business_unit_id",
            "supplier_id",
            "invoice_number",
            name="uq_core_supplier_invoice_business_unit_supplier_invoice_number",
        ),
        schema="core",
    )
    op.create_index(
        "ix_core_supplier_invoice_business_unit_id",
        "supplier_invoice",
        ["business_unit_id"],
        unique=False,
        schema="core",
    )
    op.create_index(
        "ix_core_supplier_invoice_supplier_id",
        "supplier_invoice",
        ["supplier_id"],
        unique=False,
        schema="core",
    )
    op.create_index(
        "ix_core_supplier_invoice_invoice_date",
        "supplier_invoice",
        ["invoice_date"],
        unique=False,
        schema="core",
    )

    op.create_table(
        "supplier_invoice_line",
        sa.Column("invoice_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("inventory_item_id", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column("description", sa.String(length=255), nullable=False),
        sa.Column("quantity", sa.Numeric(14, 3), nullable=False),
        sa.Column("uom_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("unit_net_amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("line_net_amount", sa.Numeric(14, 2), nullable=False),
        sa.Column(
            "id",
            sa.Uuid(as_uuid=True),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.ForeignKeyConstraint(
            ["invoice_id"],
            ["core.supplier_invoice.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["inventory_item_id"],
            ["core.inventory_item.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["uom_id"],
            ["core.unit_of_measure.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        schema="core",
    )
    op.create_index(
        "ix_core_supplier_invoice_line_invoice_id",
        "supplier_invoice_line",
        ["invoice_id"],
        unique=False,
        schema="core",
    )
    op.create_index(
        "ix_core_supplier_invoice_line_inventory_item_id",
        "supplier_invoice_line",
        ["inventory_item_id"],
        unique=False,
        schema="core",
    )


def downgrade() -> None:
    op.drop_index(
        "ix_core_supplier_invoice_line_inventory_item_id",
        table_name="supplier_invoice_line",
        schema="core",
    )
    op.drop_index(
        "ix_core_supplier_invoice_line_invoice_id",
        table_name="supplier_invoice_line",
        schema="core",
    )
    op.drop_table("supplier_invoice_line", schema="core")
    op.drop_index(
        "ix_core_supplier_invoice_invoice_date",
        table_name="supplier_invoice",
        schema="core",
    )
    op.drop_index(
        "ix_core_supplier_invoice_supplier_id",
        table_name="supplier_invoice",
        schema="core",
    )
    op.drop_index(
        "ix_core_supplier_invoice_business_unit_id",
        table_name="supplier_invoice",
        schema="core",
    )
    op.drop_table("supplier_invoice", schema="core")
