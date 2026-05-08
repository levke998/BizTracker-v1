"""Create POS product alias table.

Revision ID: 024_core_pos_product_alias
Revises: 023_core_weather_forecast_cache
Create Date: 2026-05-04
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "024_core_pos_product_alias"
down_revision = "023_core_weather_forecast_cache"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "pos_product_alias",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("business_unit_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("source_system", sa.String(length=50), nullable=False),
        sa.Column("source_product_key", sa.String(length=250), nullable=False),
        sa.Column("source_product_name", sa.String(length=250), nullable=False),
        sa.Column("source_sku", sa.String(length=100), nullable=True),
        sa.Column("source_barcode", sa.String(length=100), nullable=True),
        sa.Column(
            "status",
            sa.String(length=50),
            nullable=False,
            server_default=sa.text("'auto_created'"),
        ),
        sa.Column(
            "mapping_confidence",
            sa.String(length=50),
            nullable=False,
            server_default=sa.text("'name_auto'"),
        ),
        sa.Column(
            "occurrence_count",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_import_batch_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("last_import_row_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("notes", sa.String(length=500), nullable=True),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
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
            name="fk_core_pos_product_alias_business_unit_id_business_unit",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["product_id"],
            ["core.product.id"],
            name="fk_core_pos_product_alias_product_id_product",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["last_import_batch_id"],
            ["ingest.import_batch.id"],
            name="fk_core_pos_product_alias_last_import_batch_id_import_batch",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["last_import_row_id"],
            ["ingest.import_row.id"],
            name="fk_core_pos_product_alias_last_import_row_id_import_row",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_pos_product_alias"),
        schema="core",
    )
    op.create_index(
        "ix_core_pos_product_alias_business_unit_id",
        "pos_product_alias",
        ["business_unit_id"],
        unique=False,
        schema="core",
    )
    op.create_index(
        "ix_core_pos_product_alias_product_id",
        "pos_product_alias",
        ["product_id"],
        unique=False,
        schema="core",
    )
    op.create_index(
        "ix_core_pos_product_alias_status",
        "pos_product_alias",
        ["status"],
        unique=False,
        schema="core",
    )
    op.create_index(
        "ix_core_pos_product_alias_unique_source_key",
        "pos_product_alias",
        ["business_unit_id", "source_system", "source_product_key"],
        unique=True,
        schema="core",
    )


def downgrade() -> None:
    op.drop_index(
        "ix_core_pos_product_alias_unique_source_key",
        table_name="pos_product_alias",
        schema="core",
    )
    op.drop_index(
        "ix_core_pos_product_alias_status",
        table_name="pos_product_alias",
        schema="core",
    )
    op.drop_index(
        "ix_core_pos_product_alias_product_id",
        table_name="pos_product_alias",
        schema="core",
    )
    op.drop_index(
        "ix_core_pos_product_alias_business_unit_id",
        table_name="pos_product_alias",
        schema="core",
    )
    op.drop_table("pos_product_alias", schema="core")
