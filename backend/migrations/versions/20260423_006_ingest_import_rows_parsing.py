"""Add parse staging tables and counters to the ingest schema.

Revision ID: 006_ingest_import_rows_parsing
Revises: 005_ingest_imports_base
Create Date: 2026-04-23 09:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "006_ingest_import_rows_parsing"
down_revision = "005_ingest_imports_base"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "import_batch",
        sa.Column(
            "total_rows",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        schema="ingest",
    )
    op.add_column(
        "import_batch",
        sa.Column(
            "parsed_rows",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        schema="ingest",
    )
    op.add_column(
        "import_batch",
        sa.Column(
            "error_rows",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        schema="ingest",
    )

    op.create_table(
        "import_row",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("batch_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("file_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("row_number", sa.Integer(), nullable=False),
        sa.Column("raw_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "normalized_payload",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column("parse_status", sa.String(length=50), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(
            ["batch_id"],
            ["ingest.import_batch.id"],
            name="fk_ingest_import_row_batch_id_import_batch",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["file_id"],
            ["ingest.import_file.id"],
            name="fk_ingest_import_row_file_id_import_file",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_import_row"),
        schema="ingest",
    )
    op.create_index(
        "ix_ingest_import_row_batch_id",
        "import_row",
        ["batch_id"],
        unique=False,
        schema="ingest",
    )
    op.create_index(
        "ix_ingest_import_row_file_id",
        "import_row",
        ["file_id"],
        unique=False,
        schema="ingest",
    )
    op.create_index(
        "ix_ingest_import_row_parse_status",
        "import_row",
        ["parse_status"],
        unique=False,
        schema="ingest",
    )

    op.create_table(
        "import_row_error",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("batch_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("file_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("row_number", sa.Integer(), nullable=True),
        sa.Column("field_name", sa.String(length=100), nullable=True),
        sa.Column("error_code", sa.String(length=100), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("raw_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(
            ["batch_id"],
            ["ingest.import_batch.id"],
            name="fk_ingest_import_row_error_batch_id_import_batch",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["file_id"],
            ["ingest.import_file.id"],
            name="fk_ingest_import_row_error_file_id_import_file",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_import_row_error"),
        schema="ingest",
    )
    op.create_index(
        "ix_ingest_import_row_error_batch_id",
        "import_row_error",
        ["batch_id"],
        unique=False,
        schema="ingest",
    )
    op.create_index(
        "ix_ingest_import_row_error_file_id",
        "import_row_error",
        ["file_id"],
        unique=False,
        schema="ingest",
    )


def downgrade() -> None:
    op.drop_index(
        "ix_ingest_import_row_error_file_id",
        table_name="import_row_error",
        schema="ingest",
    )
    op.drop_index(
        "ix_ingest_import_row_error_batch_id",
        table_name="import_row_error",
        schema="ingest",
    )
    op.drop_table("import_row_error", schema="ingest")

    op.drop_index(
        "ix_ingest_import_row_parse_status",
        table_name="import_row",
        schema="ingest",
    )
    op.drop_index(
        "ix_ingest_import_row_file_id",
        table_name="import_row",
        schema="ingest",
    )
    op.drop_index(
        "ix_ingest_import_row_batch_id",
        table_name="import_row",
        schema="ingest",
    )
    op.drop_table("import_row", schema="ingest")

    op.drop_column("import_batch", "error_rows", schema="ingest")
    op.drop_column("import_batch", "parsed_rows", schema="ingest")
    op.drop_column("import_batch", "total_rows", schema="ingest")
