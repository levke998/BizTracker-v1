"""Create the financial transaction table in the core schema.

Revision ID: 007_core_financial_tx_base
Revises: 006_ingest_import_rows_parsing
Create Date: 2026-04-23 12:30:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "007_core_financial_tx_base"
down_revision = "006_ingest_import_rows_parsing"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "financial_transaction",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("business_unit_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("direction", sa.String(length=20), nullable=False),
        sa.Column("transaction_type", sa.String(length=100), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("source_type", sa.String(length=100), nullable=False),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=False),
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
            name="fk_core_financial_transaction_business_unit_id_business_unit",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_financial_transaction"),
        sa.UniqueConstraint(
            "source_type",
            "source_id",
            name="uq_core_financial_transaction_source_ref",
        ),
        schema="core",
    )
    op.create_index(
        "ix_core_financial_transaction_business_unit_id",
        "financial_transaction",
        ["business_unit_id"],
        unique=False,
        schema="core",
    )
    op.create_index(
        "ix_core_financial_transaction_occurred_at",
        "financial_transaction",
        ["occurred_at"],
        unique=False,
        schema="core",
    )
    op.create_index(
        "ix_core_financial_transaction_transaction_type",
        "financial_transaction",
        ["transaction_type"],
        unique=False,
        schema="core",
    )


def downgrade() -> None:
    op.drop_index(
        "ix_core_financial_transaction_transaction_type",
        table_name="financial_transaction",
        schema="core",
    )
    op.drop_index(
        "ix_core_financial_transaction_occurred_at",
        table_name="financial_transaction",
        schema="core",
    )
    op.drop_index(
        "ix_core_financial_transaction_business_unit_id",
        table_name="financial_transaction",
        schema="core",
    )
    op.drop_table("financial_transaction", schema="core")
