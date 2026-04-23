"""Add currency to financial transactions.

Revision ID: 008_core_financial_tx_currency
Revises: 007_core_financial_tx_base
Create Date: 2026-04-23 17:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "008_core_financial_tx_currency"
down_revision = "007_core_financial_tx_base"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "financial_transaction",
        sa.Column(
            "currency",
            sa.String(length=3),
            nullable=False,
            server_default="HUF",
        ),
        schema="core",
    )
    op.alter_column(
        "financial_transaction",
        "currency",
        server_default=None,
        schema="core",
    )


def downgrade() -> None:
    op.drop_column("financial_transaction", "currency", schema="core")
