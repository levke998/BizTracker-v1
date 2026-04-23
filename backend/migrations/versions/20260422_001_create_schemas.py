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
    op.execute("CREATE SCHEMA IF NOT EXISTS auth")
    op.execute("CREATE SCHEMA IF NOT EXISTS core")
    op.execute("CREATE SCHEMA IF NOT EXISTS ingest")
    op.execute("CREATE SCHEMA IF NOT EXISTS analytics")


def downgrade() -> None:
    op.execute("DROP SCHEMA IF EXISTS analytics")
    op.execute("DROP SCHEMA IF EXISTS ingest")
    op.execute("DROP SCHEMA IF EXISTS core")
    op.execute("DROP SCHEMA IF EXISTS auth")
