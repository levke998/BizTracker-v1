"""Add POS sale dedupe key to financial transactions.

Revision ID: 018_pos_sale_dedupe_key
Revises: 017_core_costing_foundation
Create Date: 2026-04-25
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "018_pos_sale_dedupe_key"
down_revision = "017_core_costing_foundation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "financial_transaction",
        sa.Column("dedupe_key", sa.String(128), nullable=True),
        schema="core",
    )
    op.create_index(
        "ix_core_financial_transaction_dedupe_key",
        "financial_transaction",
        ["dedupe_key"],
        unique=True,
        schema="core",
    )


def downgrade() -> None:
    op.drop_index(
        "ix_core_financial_transaction_dedupe_key",
        table_name="financial_transaction",
        schema="core",
    )
    op.drop_column("financial_transaction", "dedupe_key", schema="core")
