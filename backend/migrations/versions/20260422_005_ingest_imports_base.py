"""Create import metadata tables in the ingest schema.

Revision ID: 005_ingest_imports_base
Revises: 004_core_category_product_base
Create Date: 2026-04-22 22:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "005_ingest_imports_base"
down_revision = "004_core_category_product_base"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "import_batch",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("business_unit_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("import_type", sa.String(length=100), nullable=False),
        sa.Column(
            "status",
            sa.String(length=50),
            nullable=False,
            server_default=sa.text("'uploaded'"),
        ),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
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
            name="fk_ingest_import_batch_business_unit_id_business_unit",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_import_batch"),
        schema="ingest",
    )
    op.create_index(
        "ix_ingest_import_batch_business_unit_id",
        "import_batch",
        ["business_unit_id"],
        unique=False,
        schema="ingest",
    )
    op.create_index(
        "ix_ingest_import_batch_status",
        "import_batch",
        ["status"],
        unique=False,
        schema="ingest",
    )
    op.create_index(
        "ix_ingest_import_batch_created_at",
        "import_batch",
        ["created_at"],
        unique=False,
        schema="ingest",
    )

    op.create_table(
        "import_file",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("batch_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("original_name", sa.String(length=255), nullable=False),
        sa.Column("stored_path", sa.String(length=500), nullable=False),
        sa.Column("mime_type", sa.String(length=255), nullable=True),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column(
            "uploaded_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(
            ["batch_id"],
            ["ingest.import_batch.id"],
            name="fk_ingest_import_file_batch_id_import_batch",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_import_file"),
        schema="ingest",
    )
    op.create_index(
        "ix_ingest_import_file_batch_id",
        "import_file",
        ["batch_id"],
        unique=False,
        schema="ingest",
    )


def downgrade() -> None:
    op.drop_index(
        "ix_ingest_import_file_batch_id",
        table_name="import_file",
        schema="ingest",
    )
    op.drop_table("import_file", schema="ingest")

    op.drop_index(
        "ix_ingest_import_batch_created_at",
        table_name="import_batch",
        schema="ingest",
    )
    op.drop_index(
        "ix_ingest_import_batch_status",
        table_name="import_batch",
        schema="ingest",
    )
    op.drop_index(
        "ix_ingest_import_batch_business_unit_id",
        table_name="import_batch",
        schema="ingest",
    )
    op.drop_table("import_batch", schema="ingest")
