"""Create base identity tables in the auth schema.

Revision ID: 002_auth_identity_base
Revises: 001_create_schemas
Create Date: 2026-04-22 18:31:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "002_auth_identity_base"
down_revision = "001_create_schemas"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=200), nullable=False),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.PrimaryKeyConstraint("id", name="pk_user"),
        sa.UniqueConstraint("email", name="uq_auth_user_email"),
        schema="auth",
    )
    op.create_index(
        "ix_auth_user_email",
        "user",
        ["email"],
        unique=False,
        schema="auth",
    )

    op.create_table(
        "role",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
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
        sa.PrimaryKeyConstraint("id", name="pk_role"),
        sa.UniqueConstraint("code", name="uq_auth_role_code"),
        schema="auth",
    )
    op.create_index(
        "ix_auth_role_code",
        "role",
        ["code"],
        unique=False,
        schema="auth",
    )

    op.create_table(
        "permission",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("code", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
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
        sa.PrimaryKeyConstraint("id", name="pk_permission"),
        sa.UniqueConstraint("code", name="uq_auth_permission_code"),
        schema="auth",
    )
    op.create_index(
        "ix_auth_permission_code",
        "permission",
        ["code"],
        unique=False,
        schema="auth",
    )

    op.create_table(
        "user_role",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "assigned_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["auth.user.id"],
            name="fk_auth_user_role_user_id_user",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["role_id"],
            ["auth.role.id"],
            name="fk_auth_user_role_role_id_role",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("user_id", "role_id", name="pk_user_role"),
        schema="auth",
    )
    op.create_index(
        "ix_auth_user_role_role_id",
        "user_role",
        ["role_id"],
        unique=False,
        schema="auth",
    )

    op.create_table(
        "role_permission",
        sa.Column("role_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("permission_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "assigned_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(
            ["role_id"],
            ["auth.role.id"],
            name="fk_auth_role_permission_role_id_role",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["permission_id"],
            ["auth.permission.id"],
            name="fk_auth_role_permission_permission_id_permission",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "role_id",
            "permission_id",
            name="pk_role_permission",
        ),
        schema="auth",
    )
    op.create_index(
        "ix_auth_role_permission_permission_id",
        "role_permission",
        ["permission_id"],
        unique=False,
        schema="auth",
    )


def downgrade() -> None:
    op.drop_index(
        "ix_auth_role_permission_permission_id",
        table_name="role_permission",
        schema="auth",
    )
    op.drop_table("role_permission", schema="auth")

    op.drop_index(
        "ix_auth_user_role_role_id",
        table_name="user_role",
        schema="auth",
    )
    op.drop_table("user_role", schema="auth")

    op.drop_index(
        "ix_auth_permission_code",
        table_name="permission",
        schema="auth",
    )
    op.drop_table("permission", schema="auth")

    op.drop_index("ix_auth_role_code", table_name="role", schema="auth")
    op.drop_table("role", schema="auth")

    op.drop_index("ix_auth_user_email", table_name="user", schema="auth")
    op.drop_table("user", schema="auth")
