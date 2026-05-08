"""Create supplier invoice PDF draft table.

Revision ID: 026_core_supplier_invoice_draft
Revises: 025_core_product_sale_price_observation
Create Date: 2026-05-04
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "026_core_supplier_invoice_draft"
down_revision = "025_core_product_sale_price_observation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "supplier_invoice_draft",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("business_unit_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("supplier_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("original_name", sa.String(length=255), nullable=False),
        sa.Column("stored_path", sa.String(length=500), nullable=False),
        sa.Column("mime_type", sa.String(length=255), nullable=True),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column(
            "status",
            sa.String(length=50),
            nullable=False,
            server_default=sa.text("'review_required'"),
        ),
        sa.Column(
            "extraction_status",
            sa.String(length=50),
            nullable=False,
            server_default=sa.text("'not_started'"),
        ),
        sa.Column("raw_extraction", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("review_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
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
            name="fk_core_supplier_invoice_draft_business_unit_id_business_unit",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["supplier_id"],
            ["core.supplier.id"],
            name="fk_core_supplier_invoice_draft_supplier_id_supplier",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_supplier_invoice_draft"),
        schema="core",
    )
    op.create_index(
        "ix_core_supplier_invoice_draft_business_unit_id",
        "supplier_invoice_draft",
        ["business_unit_id"],
        unique=False,
        schema="core",
    )
    op.create_index(
        "ix_core_supplier_invoice_draft_supplier_id",
        "supplier_invoice_draft",
        ["supplier_id"],
        unique=False,
        schema="core",
    )
    op.create_index(
        "ix_core_supplier_invoice_draft_status",
        "supplier_invoice_draft",
        ["status"],
        unique=False,
        schema="core",
    )


def downgrade() -> None:
    op.drop_index(
        "ix_core_supplier_invoice_draft_status",
        table_name="supplier_invoice_draft",
        schema="core",
    )
    op.drop_index(
        "ix_core_supplier_invoice_draft_supplier_id",
        table_name="supplier_invoice_draft",
        schema="core",
    )
    op.drop_index(
        "ix_core_supplier_invoice_draft_business_unit_id",
        table_name="supplier_invoice_draft",
        schema="core",
    )
    op.drop_table("supplier_invoice_draft", schema="core")
