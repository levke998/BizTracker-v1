"""Create supplier table in the core schema.

Revision ID: 013_core_supplier_base
Revises: 012_inventory_movement_note
Create Date: 2026-04-23
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "013_core_supplier_base"
down_revision = "012_inventory_movement_note"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "supplier",
        sa.Column("business_unit_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=180), nullable=False),
        sa.Column("tax_id", sa.String(length=80), nullable=True),
        sa.Column("contact_name", sa.String(length=150), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("phone", sa.String(length=80), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
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
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "business_unit_id",
            "name",
            name="uq_core_supplier_business_unit_name",
        ),
        schema="core",
    )
    op.create_index(
        "ix_core_supplier_business_unit_id",
        "supplier",
        ["business_unit_id"],
        unique=False,
        schema="core",
    )
    op.create_index(
        "ix_core_supplier_name",
        "supplier",
        ["name"],
        unique=False,
        schema="core",
    )


def downgrade() -> None:
    op.drop_index("ix_core_supplier_name", table_name="supplier", schema="core")
    op.drop_index(
        "ix_core_supplier_business_unit_id",
        table_name="supplier",
        schema="core",
    )
    op.drop_table("supplier", schema="core")
