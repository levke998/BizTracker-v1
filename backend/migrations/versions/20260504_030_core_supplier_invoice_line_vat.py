"""Add VAT fields to supplier invoice lines.

Revision ID: 030_core_supplier_invoice_line_vat
Revises: 029_core_default_vat_links
Create Date: 2026-05-04 16:45:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "030_core_supplier_invoice_line_vat"
down_revision: Union[str, None] = "029_core_default_vat_links"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "supplier_invoice_line",
        sa.Column("vat_rate_id", sa.Uuid(as_uuid=True), nullable=True),
        schema="core",
    )
    op.add_column(
        "supplier_invoice_line",
        sa.Column("vat_amount", sa.Numeric(14, 2), nullable=True),
        schema="core",
    )
    op.add_column(
        "supplier_invoice_line",
        sa.Column("line_gross_amount", sa.Numeric(14, 2), nullable=True),
        schema="core",
    )
    op.create_foreign_key(
        "fk_core_supplier_invoice_line_vat_rate_id",
        "supplier_invoice_line",
        "vat_rate",
        ["vat_rate_id"],
        ["id"],
        source_schema="core",
        referent_schema="core",
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_core_supplier_invoice_line_vat_rate_id",
        "supplier_invoice_line",
        ["vat_rate_id"],
        unique=False,
        schema="core",
    )


def downgrade() -> None:
    op.drop_index(
        "ix_core_supplier_invoice_line_vat_rate_id",
        table_name="supplier_invoice_line",
        schema="core",
    )
    op.drop_constraint(
        "fk_core_supplier_invoice_line_vat_rate_id",
        "supplier_invoice_line",
        schema="core",
        type_="foreignkey",
    )
    op.drop_column("supplier_invoice_line", "line_gross_amount", schema="core")
    op.drop_column("supplier_invoice_line", "vat_amount", schema="core")
    op.drop_column("supplier_invoice_line", "vat_rate_id", schema="core")
