"""Create VAT rate reference table.

Revision ID: 027_core_vat_rate
Revises: 026_core_supplier_invoice_draft
Create Date: 2026-05-04 15:10:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "027_core_vat_rate"
down_revision: Union[str, None] = "026_core_supplier_invoice_draft"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


vat_rate_table = sa.table(
    "vat_rate",
    sa.column("id", sa.Uuid(as_uuid=True)),
    sa.column("code", sa.String),
    sa.column("name", sa.String),
    sa.column("rate_percent", sa.Numeric),
    sa.column("rate_type", sa.String),
    sa.column("nav_code", sa.String),
    sa.column("description", sa.Text),
    sa.column("valid_from", sa.Date),
    sa.column("is_active", sa.Boolean),
)


def upgrade() -> None:
    op.create_table(
        "vat_rate",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("code", sa.String(length=40), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("rate_percent", sa.Numeric(7, 4), nullable=False),
        sa.Column(
            "rate_type",
            sa.String(length=40),
            server_default=sa.text("'standard'"),
            nullable=False,
        ),
        sa.Column("nav_code", sa.String(length=80), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("valid_from", sa.Date(), nullable=True),
        sa.Column("valid_to", sa.Date(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_core_vat_rate_code"),
        schema="core",
    )
    op.create_index(
        "ix_core_vat_rate_is_active",
        "vat_rate",
        ["is_active"],
        unique=False,
        schema="core",
    )

    op.execute(
        """
        INSERT INTO core.vat_rate
            (id, code, name, rate_percent, rate_type, nav_code, description, valid_from, is_active)
        VALUES
            (gen_random_uuid(), 'HU_27', '27% AFA', 27.0000, 'standard', 'VAT27', 'Magyar altalanos AFA kulcs.', DATE '2012-01-01', true),
            (gen_random_uuid(), 'HU_18', '18% AFA', 18.0000, 'reduced', 'VAT18', 'Magyar kedvezmenyes AFA kulcs meghatarozott termekekre/szolgaltatasokra.', DATE '2006-09-01', true),
            (gen_random_uuid(), 'HU_5', '5% AFA', 5.0000, 'reduced', 'VAT5', 'Magyar kedvezmenyes AFA kulcs meghatarozott termekekre/szolgaltatasokra.', DATE '2006-09-01', true),
            (gen_random_uuid(), 'HU_0', '0% AFA', 0.0000, 'zero', 'VAT0', 'Magyar 0%-os adomertek, peldaul 2024-tol meghatarozott napilapokra.', DATE '2024-01-01', true),
            (gen_random_uuid(), 'HU_EXEMPT', 'Adomentes', 0.0000, 'exempt', 'EXEMPT', 'Adomentes vagy AFA hatalyan kivuli jellegu sor, csak review utan hasznalhato.', NULL, true),
            (gen_random_uuid(), 'HU_REVERSE', 'Forditott adozas', 0.0000, 'reverse_charge', 'REVERSE', 'Forditott adozas jeloles, szamla review es konyvelesi kontroll mellett.', NULL, true)
        """
    )


def downgrade() -> None:
    op.drop_index("ix_core_vat_rate_is_active", table_name="vat_rate", schema="core")
    op.drop_table("vat_rate", schema="core")
