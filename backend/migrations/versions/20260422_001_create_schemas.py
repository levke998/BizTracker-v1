"""Create PostgreSQL schemas used by the application.

Revision ID: 001_create_schemas
Revises:
Create Date: 2026-04-22 18:30:00
"""

from __future__ import annotations

from alembic import op

# revision identifiers, used by Alembic.
revision = "001_create_schemas"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Alembic creates this table before running the first revision. Later
    # BizTracker revision identifiers exceed Alembic's default VARCHAR(32).
    op.execute(
        "ALTER TABLE alembic_version "
        "ALTER COLUMN version_num TYPE VARCHAR(64)"
    )
    op.execute("CREATE SCHEMA IF NOT EXISTS auth")
    op.execute("CREATE SCHEMA IF NOT EXISTS core")
    op.execute("CREATE SCHEMA IF NOT EXISTS ingest")
    op.execute("CREATE SCHEMA IF NOT EXISTS analytics")


def downgrade() -> None:
    op.execute("DROP SCHEMA IF EXISTS analytics")
    op.execute("DROP SCHEMA IF EXISTS ingest")
    op.execute("DROP SCHEMA IF EXISTS core")
    op.execute("DROP SCHEMA IF EXISTS auth")
