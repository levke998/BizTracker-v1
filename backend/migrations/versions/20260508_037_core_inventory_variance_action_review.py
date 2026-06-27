"""Add inventory variance action review state.

Revision ID: 037_core_inventory_variance_action_review
Revises: 036_core_event_performer_settlement_type
Create Date: 2026-05-08 00:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "037_core_inventory_variance_action_review"
down_revision = "036_core_event_performer_settlement_type"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "inventory_variance_action_review",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("business_unit_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("suggestion_id", sa.String(length=220), nullable=False),
        sa.Column(
            "status",
            sa.String(length=30),
            server_default=sa.text("'open'"),
            nullable=False,
        ),
        sa.Column("note", sa.String(length=500), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["business_unit_id"],
            ["core.business_unit.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "business_unit_id",
            "suggestion_id",
            name="uq_core_inventory_variance_action_review_unit_suggestion",
        ),
        schema="core",
    )
    op.create_index(
        "ix_core_inventory_variance_action_review_business_unit_id",
        "inventory_variance_action_review",
        ["business_unit_id"],
        unique=False,
        schema="core",
    )
    op.create_index(
        "ix_core_inventory_variance_action_review_suggestion_id",
        "inventory_variance_action_review",
        ["suggestion_id"],
        unique=False,
        schema="core",
    )


def downgrade() -> None:
    op.drop_index(
        "ix_core_inventory_variance_action_review_suggestion_id",
        table_name="inventory_variance_action_review",
        schema="core",
    )
    op.drop_index(
        "ix_core_inventory_variance_action_review_business_unit_id",
        table_name="inventory_variance_action_review",
        schema="core",
    )
    op.drop_table("inventory_variance_action_review", schema="core")
