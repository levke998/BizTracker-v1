"""Add inventory variance threshold configuration.

Revision ID: 034_core_inventory_variance_threshold
Revises: 033_core_inventory_movement_reason
Create Date: 2026-05-07 00:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "034_core_inventory_variance_threshold"
down_revision = "033_core_inventory_movement_reason"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "inventory_variance_threshold",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("business_unit_id", sa.Uuid(), nullable=False),
        sa.Column(
            "high_loss_value_threshold",
            sa.Numeric(14, 2),
            nullable=False,
            server_default=sa.text("10000.00"),
        ),
        sa.Column(
            "worsening_percent_threshold",
            sa.Numeric(7, 2),
            nullable=False,
            server_default=sa.text("25.00"),
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(
            ["business_unit_id"],
            ["core.business_unit.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "business_unit_id",
            name="uq_core_inventory_variance_threshold_business_unit_id",
        ),
        schema="core",
    )
    op.create_index(
        "ix_core_inventory_variance_threshold_business_unit_id",
        "inventory_variance_threshold",
        ["business_unit_id"],
        unique=False,
        schema="core",
    )


def downgrade() -> None:
    op.drop_index(
        "ix_core_inventory_variance_threshold_business_unit_id",
        table_name="inventory_variance_threshold",
        schema="core",
    )
    op.drop_table("inventory_variance_threshold", schema="core")
