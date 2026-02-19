"""Consolidated baseline schema and seed data.

Revision ID: 20260216_0001
Revises:
Create Date: 2026-02-16 00:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union
import os
import uuid

from alembic import op
from dotenv import load_dotenv
from passlib.context import CryptContext
import sqlalchemy as sa
from sqlalchemy.dialects import mssql
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER


# revision identifiers, used by Alembic.
revision: str = "20260216_0001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _load_admin_password() -> str:
    load_dotenv()
    admin_password = os.getenv("ADMIN_PASSWORD")
    if not admin_password:
        raise ValueError("Missing configuration value 'ADMIN_PASSWORD'")
    return admin_password


def upgrade() -> None:
    """Upgrade schema and seed catalogs."""
    op.create_table(
        "services",
        sa.Column("id", UNIQUEIDENTIFIER(as_uuid=True), nullable=False),
        sa.Column(
            "name",
            sa.String(length=50),
            nullable=False,
            comment="Service name used for RBAC scoping",
        ),
        sa.Column(
            "description",
            sa.String(length=255),
            nullable=True,
            comment="Service description",
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("1"),
            comment="Whether this service is active",
        ),
        sa.Column(
            "url",
            sa.String(length=255),
            nullable=True,
            comment="Base URL for the service",
        ),
        sa.Column(
            "port",
            sa.Integer(),
            nullable=True,
            comment="Network port for the service",
        ),
        sa.Column(
            "created_at",
            mssql.DATETIME2(precision=6),
            nullable=False,
            server_default=sa.text("SYSUTCDATETIME()"),
        ),
        sa.Column(
            "updated_at",
            mssql.DATETIME2(precision=6),
            nullable=False,
            server_default=sa.text("SYSUTCDATETIME()"),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", name="uix_services_name"),
    )
    op.create_index("ix_services_name", "services", ["name"], unique=False)

    op.create_table(
        "roles",
        sa.Column("id", UNIQUEIDENTIFIER(as_uuid=True), nullable=False),
        sa.Column("service_id", UNIQUEIDENTIFIER(as_uuid=True), nullable=False, comment="Service identifier this role belongs to"),
        sa.Column(
            "name",
            sa.String(length=50),
            nullable=False,
            comment="Role name within the service (e.g., 'admin', 'user', 'translator')",
        ),
        sa.Column("description", sa.String(length=200), nullable=False),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            comment="Whether this role is currently active and can be assigned",
        ),
        sa.Column(
            "created_at",
            mssql.DATETIME2(precision=6),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["service_id"],
            ["services.id"],
            ondelete="NO ACTION",
            onupdate="NO ACTION",
            name="fk_roles_service_id",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("service_id", "name", name="uix_service_role_name"),
    )
    op.create_index("ix_roles_service_id", "roles", ["service_id"], unique=False)

    op.create_table(
        "permissions",
        sa.Column("id", UNIQUEIDENTIFIER(as_uuid=True), nullable=False),
        sa.Column("service_id", UNIQUEIDENTIFIER(as_uuid=True), nullable=False, comment="Service identifier this permission belongs to"),
        sa.Column(
            "name",
            sa.String(length=50),
            nullable=False,
            comment="Human-readable permission name",
        ),
        sa.Column(
            "resource",
            sa.String(length=50),
            nullable=False,
            comment="Resource type (e.g., 'user', 'translation', 'document')",
        ),
        sa.Column(
            "action",
            sa.String(length=30),
            nullable=False,
            comment="Action type (e.g., 'create', 'read', 'update', 'delete')",
        ),
        sa.Column("description", sa.String(length=200), nullable=True),
        sa.Column(
            "created_at",
            mssql.DATETIME2(precision=6),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["service_id"],
            ["services.id"],
            ondelete="NO ACTION",
            onupdate="NO ACTION",
            name="fk_permissions_service_id",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "service_id", "resource", "action", name="uix_service_permission"
        ),
    )
    op.create_index(
        "ix_permission_service_id", "permissions", ["service_id"], unique=False
    )

    op.create_table(
        "users",
        sa.Column("id", UNIQUEIDENTIFIER(as_uuid=True), nullable=False),
        sa.Column("first_name", sa.String(length=50), nullable=False),
        sa.Column("middle_name", sa.String(length=50), nullable=True),
        sa.Column("last_name", sa.String(length=50), nullable=False),
        sa.Column("email", sa.String(length=250), nullable=False),
        sa.Column("hashed_password", sa.String(length=200), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("is_verified", sa.Boolean(), nullable=False),
        sa.Column(
            "failed_login_attempts",
            sa.Integer(),
            nullable=False,
            server_default="0",
            comment="Number of consecutive failed login attempts",
        ),
        sa.Column(
            "locked_until",
            mssql.DATETIME2(precision=6),
            nullable=True,
            comment="Timestamp until which the account is locked",
        ),
        sa.Column(
            "created_at",
            mssql.DATETIME2(precision=6),
            server_default=sa.text("SYSDATETIMEOFFSET()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            mssql.DATETIME2(precision=6),
            server_default=sa.text("SYSDATETIMEOFFSET()"),
            nullable=False,
        ),
        sa.Column(
            "is_deleted",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    op.create_table(
        "refresh_tokens",
        sa.Column("id", UNIQUEIDENTIFIER(as_uuid=True), nullable=False),
        sa.Column("user_id", UNIQUEIDENTIFIER(as_uuid=True), nullable=False),
        sa.Column("token_hashed", sa.String(length=255), nullable=False),
        sa.Column("expires_at", mssql.DATETIME2(precision=6), nullable=False),
        sa.Column("revoked", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            mssql.DATETIME2(precision=6),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("revoked_at", mssql.DATETIME2(precision=6), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_refresh_tokens_expires_at",
        "refresh_tokens",
        ["expires_at"],
        unique=False,
    )
    op.create_index(
        "ix_refresh_tokens_user_id",
        "refresh_tokens",
        ["user_id"],
        unique=False,
    )

    op.create_table(
        "role_permissions",
        sa.Column("id", UNIQUEIDENTIFIER(as_uuid=True), nullable=False),
        sa.Column("role_id", UNIQUEIDENTIFIER(as_uuid=True), nullable=False),
        sa.Column("permission_id", UNIQUEIDENTIFIER(as_uuid=True), nullable=False),
        sa.Column(
            "assigned_at",
            mssql.DATETIME2(precision=6),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["permission_id"], ["permissions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("role_id", "permission_id", name="uix_role_permission"),
    )
    op.create_index(
        "ix_role_permissions_permission_id",
        "role_permissions",
        ["permission_id"],
        unique=False,
    )
    op.create_index(
        "ix_role_permissions_role_id",
        "role_permissions",
        ["role_id"],
        unique=False,
    )

    op.create_table(
        "user_permissions",
        sa.Column("id", UNIQUEIDENTIFIER(as_uuid=True), nullable=False),
        sa.Column("user_id", UNIQUEIDENTIFIER(as_uuid=True), nullable=False),
        sa.Column("permission_id", UNIQUEIDENTIFIER(as_uuid=True), nullable=False),
        sa.Column(
            "assigned_at",
            mssql.DATETIME2(precision=6),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "expires_at",
            mssql.DATETIME2(precision=6),
            nullable=True,
            comment="Optional expiration for temporary permissions",
        ),
        sa.ForeignKeyConstraint(["permission_id"], ["permissions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "permission_id", name="uix_user_permission"),
    )
    op.create_index(
        "ix_user_permissions_permission_id",
        "user_permissions",
        ["permission_id"],
        unique=False,
    )
    op.create_index(
        "ix_user_permissions_user_id",
        "user_permissions",
        ["user_id"],
        unique=False,
    )

    op.create_table(
        "user_roles",
        sa.Column("id", UNIQUEIDENTIFIER(as_uuid=True), nullable=False),
        sa.Column("user_id", UNIQUEIDENTIFIER(as_uuid=True), nullable=False),
        sa.Column("role_id", UNIQUEIDENTIFIER(as_uuid=True), nullable=False),
        sa.Column(
            "assigned_at",
            mssql.DATETIME2(precision=6),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "role_id", name="uix_user_role"),
    )
    op.create_index("ix_user_role_role_id", "user_roles", ["role_id"], unique=False)
    op.create_index("ix_user_role_user_id", "user_roles", ["user_id"], unique=False)

    op.create_table(
        "user_services",
        sa.Column("id", UNIQUEIDENTIFIER(as_uuid=True), nullable=False, primary_key=True),
        sa.Column("user_id", UNIQUEIDENTIFIER(as_uuid=True), nullable=False),
        sa.Column("service_id", UNIQUEIDENTIFIER(as_uuid=True), nullable=False),
        sa.Column(
            "assigned_at",
            mssql.DATETIME2(precision=6),
            server_default=sa.text("SYSDATETIMEOFFSET()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE", onupdate="NO ACTION"),
        sa.ForeignKeyConstraint(
            ["service_id"],
            ["services.id"],
            ondelete="CASCADE",
            onupdate="NO ACTION",
        ),
        sa.UniqueConstraint("user_id", "service_id", name="uix_user_service"),
    )
    op.create_index(
        "ix_user_service_user_id", "user_services", ["user_id"], unique=False
    )
    op.create_index(
        "ix_user_service_service_id", "user_services", ["service_id"], unique=False
    )

    admin_password = _load_admin_password()
    admin_hashed_password = CryptContext(schemes=["bcrypt"]).hash(admin_password)

    services_table = sa.table(
        "services",
        sa.column("id", UNIQUEIDENTIFIER(as_uuid=True)),
        sa.column("name", sa.String(50)),
        sa.column("description", sa.String(255)),
        sa.column("is_active", sa.Boolean),
        sa.column("url", sa.String(255)),
        sa.column("port", sa.Integer),
    )

    roles_table = sa.table(
        "roles",
        sa.column("id", UNIQUEIDENTIFIER(as_uuid=True)),
        sa.column("service_id", UNIQUEIDENTIFIER(as_uuid=True)),
        sa.column("name", sa.String(50)),
        sa.column("description", sa.String(200)),
        sa.column("is_active", sa.Boolean),
    )

    permissions_table = sa.table(
        "permissions",
        sa.column("id", UNIQUEIDENTIFIER(as_uuid=True)),
        sa.column("service_id", UNIQUEIDENTIFIER(as_uuid=True)),
        sa.column("name", sa.String(50)),
        sa.column("resource", sa.String(50)),
        sa.column("action", sa.String(30)),
        sa.column("description", sa.String(200)),
    )

    role_permissions_table = sa.table(
        "role_permissions",
        sa.column("id", UNIQUEIDENTIFIER(as_uuid=True)),
        sa.column("role_id", UNIQUEIDENTIFIER(as_uuid=True)),
        sa.column("permission_id", UNIQUEIDENTIFIER(as_uuid=True)),
    )

    users_table = sa.table(
        "users",
        sa.column("id", UNIQUEIDENTIFIER(as_uuid=True)),
        sa.column("first_name", sa.String(50)),
        sa.column("middle_name", sa.String(50)),
        sa.column("last_name", sa.String(50)),
        sa.column("email", sa.String(250)),
        sa.column("hashed_password", sa.String(200)),
        sa.column("is_active", sa.Boolean),
        sa.column("is_verified", sa.Boolean),
        sa.column("failed_login_attempts", sa.Integer),
        sa.column("locked_until", sa.DateTime(timezone=True)),
        sa.column("is_deleted", sa.Boolean),
    )

    user_roles_table = sa.table(
        "user_roles",
        sa.column("id", UNIQUEIDENTIFIER(as_uuid=True)),
        sa.column("user_id", UNIQUEIDENTIFIER(as_uuid=True)),
        sa.column("role_id", UNIQUEIDENTIFIER(as_uuid=True)),
    )

    user_services_table = sa.table(
        "user_services",
        sa.column("id", UNIQUEIDENTIFIER(as_uuid=True)),
        sa.column("user_id", UNIQUEIDENTIFIER(as_uuid=True)),
        sa.column("service_id", UNIQUEIDENTIFIER(as_uuid=True)),
    )

    service_id = uuid.uuid4()
    admin_role_id = uuid.uuid4()
    user_role_id = uuid.uuid4()
    admin_user_id = uuid.uuid4()

    op.bulk_insert(
        services_table,
        [
            {
                "id": service_id,
                "name": "identity-service",
                "description": "Identity service",
                "is_active": True,
                "url": None,
                "port": None,
            }
        ],
    )

    op.bulk_insert(
        roles_table,
        [
            {
                "id": admin_role_id,
                "service_id": service_id,
                "name": "admin",
                "description": "Administrator with full system access",
                "is_active": True,
            },
            {
                "id": user_role_id,
                "service_id": service_id,
                "name": "user",
                "description": "Standard user with limited access",
                "is_active": True,
            },
        ],
    )

    permissions_data = [
        {
            "id": uuid.uuid4(),
            "service_id": service_id,
            "name": "Create User",
            "resource": "user",
            "action": "create",
            "description": "Permission to create new users",
        },
        {
            "id": uuid.uuid4(),
            "service_id": service_id,
            "name": "Read User",
            "resource": "user",
            "action": "read",
            "description": "Permission to view user information",
        },
        {
            "id": uuid.uuid4(),
            "service_id": service_id,
            "name": "Update User",
            "resource": "user",
            "action": "update",
            "description": "Permission to update user information",
        },
        {
            "id": uuid.uuid4(),
            "service_id": service_id,
            "name": "Delete User",
            "resource": "user",
            "action": "delete",
            "description": "Permission to delete users",
        },
        {
            "id": uuid.uuid4(),
            "service_id": service_id,
            "name": "Assign Roles",
            "resource": "role",
            "action": "assign",
            "description": "Permission to assign roles to users",
        },
        {
            "id": uuid.uuid4(),
            "service_id": service_id,
            "name": "Assign Permissions",
            "resource": "permission",
            "action": "assign",
            "description": "Permission to assign permissions to users or roles",
        },
        {
            "id": uuid.uuid4(),
            "service_id": service_id,
            "name": "Read Own Profile",
            "resource": "profile",
            "action": "read",
            "description": "Permission to view own profile",
        },
        {
            "id": uuid.uuid4(),
            "service_id": service_id,
            "name": "Update Own Profile",
            "resource": "profile",
            "action": "update",
            "description": "Permission to update own profile",
        },
        {
            "id": uuid.uuid4(),
            "service_id": service_id,
            "name": "Refresh Token",
            "resource": "auth",
            "action": "refresh",
            "description": "Permission to refresh authentication tokens",
        },
        {
            "id": uuid.uuid4(),
            "service_id": service_id,
            "name": "Create Service",
            "resource": "service",
            "action": "create",
            "description": "Permission to create new services",
        },
        {
            "id": uuid.uuid4(),
            "service_id": service_id,
            "name": "Read Service",
            "resource": "service",
            "action": "read",
            "description": "Permission to view service information",
        },
        {
            "id": uuid.uuid4(),
            "service_id": service_id,
            "name": "Update Service",
            "resource": "service",
            "action": "update",
            "description": "Permission to update service information",
        },
        {
            "id": uuid.uuid4(),
            "service_id": service_id,
            "name": "Delete Service",
            "resource": "service",
            "action": "delete",
            "description": "Permission to delete services",
        },
        {
            "id": uuid.uuid4(),
            "service_id": service_id,
            "name": "Create Role",
            "resource": "role",
            "action": "create",
            "description": "Permission to create new roles",
        },
        {
            "id": uuid.uuid4(),
            "service_id": service_id,
            "name": "Read Role",
            "resource": "role",
            "action": "read",
            "description": "Permission to view role information",
        },
        {
            "id": uuid.uuid4(),
            "service_id": service_id,
            "name": "Update Role",
            "resource": "role",
            "action": "update",
            "description": "Permission to update role information",
        },
        {
            "id": uuid.uuid4(),
            "service_id": service_id,
            "name": "Delete Role",
            "resource": "role",
            "action": "delete",
            "description": "Permission to delete roles",
        },
        {
            "id": uuid.uuid4(),
            "service_id": service_id,
            "name": "Create Permission",
            "resource": "permission",
            "action": "create",
            "description": "Permission to create new permissions",
        },
        {
            "id": uuid.uuid4(),
            "service_id": service_id,
            "name": "Read Permission",
            "resource": "permission",
            "action": "read",
            "description": "Permission to view permission information",
        },
        {
            "id": uuid.uuid4(),
            "service_id": service_id,
            "name": "Update Permission",
            "resource": "permission",
            "action": "update",
            "description": "Permission to update permission information and role assignments",
        },
        {
            "id": uuid.uuid4(),
            "service_id": service_id,
            "name": "Delete Permission",
            "resource": "permission",
            "action": "delete",
            "description": "Permission to delete permissions",
        },
    ]

    op.bulk_insert(permissions_table, permissions_data)

    admin_role_permissions = [
        {
            "id": uuid.uuid4(),
            "role_id": admin_role_id,
            "permission_id": permission["id"],
        }
        for permission in permissions_data
    ]
    op.bulk_insert(role_permissions_table, admin_role_permissions)

    user_role_permissions = [
        {
            "id": uuid.uuid4(),
            "role_id": user_role_id,
            "permission_id": permission["id"],
        }
        for permission in permissions_data
        if permission["resource"] in {"profile", "auth"}
        or (permission["resource"] == "user" and permission["action"] == "read")
    ]
    op.bulk_insert(role_permissions_table, user_role_permissions)

    op.bulk_insert(
        users_table,
        [
            {
                "id": admin_user_id,
                "first_name": "System",
                "middle_name": None,
                "last_name": "Administrator",
                "email": "admin@email.com",
                "hashed_password": admin_hashed_password,
                "is_active": True,
                "is_verified": True,
                "failed_login_attempts": 0,
                "locked_until": None,
                "is_deleted": False,
            }
        ],
    )

    op.bulk_insert(
        user_roles_table,
        [
            {
                "id": uuid.uuid4(),
                "user_id": admin_user_id,
                "role_id": admin_role_id,
            }
        ],
    )

    op.bulk_insert(
        user_services_table,
        [
            {
                "id": uuid.uuid4(),
                "user_id": admin_user_id,
                "service_id": service_id,
            }
        ],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_user_service_service_id", table_name="user_services")
    op.drop_index("ix_user_service_user_id", table_name="user_services")
    op.drop_table("user_services")

    op.drop_index("ix_user_role_user_id", table_name="user_roles")
    op.drop_index("ix_user_role_role_id", table_name="user_roles")
    op.drop_table("user_roles")

    op.drop_index("ix_user_permissions_user_id", table_name="user_permissions")
    op.drop_index("ix_user_permissions_permission_id", table_name="user_permissions")
    op.drop_table("user_permissions")

    op.drop_index("ix_role_permissions_role_id", table_name="role_permissions")
    op.drop_index("ix_role_permissions_permission_id", table_name="role_permissions")
    op.drop_table("role_permissions")

    op.drop_index("ix_refresh_tokens_user_id", table_name="refresh_tokens")
    op.drop_index("ix_refresh_tokens_expires_at", table_name="refresh_tokens")
    op.drop_table("refresh_tokens")

    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")

    op.drop_index("ix_permission_service_id", table_name="permissions")
    op.drop_table("permissions")

    op.drop_index("ix_roles_service_id", table_name="roles")
    op.drop_table("roles")

    op.drop_index("ix_services_name", table_name="services")
    op.drop_table("services")