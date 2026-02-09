"""seed_initial_catalogs

Revision ID: 58218a941040
Revises: cb785e7a7c01
Create Date: 2026-01-16 22:34:12.576242

"""
from typing import Sequence, Union
from datetime import datetime, UTC

from alembic import op
from dotenv import load_dotenv
import os
import sqlalchemy as sa
import uuid
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER

load_dotenv()

admin_password = os.getenv("ADMIN_PASSWORD")
from passlib.context import CryptContext; 

if admin_password is None:
    raise Exception("Missing configuration value 'admin_password'")

admin_hashed_password = CryptContext(schemes=['bcrypt']).hash(admin_password)

# revision identifiers, used by Alembic.
revision: str = '58218a941040'
down_revision: Union[str, Sequence[str], None] = 'cb785e7a7c01'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - insert seed data."""
    # Create table references
    roles_table = sa.table(
        'roles',
        sa.column('id', UNIQUEIDENTIFIER(as_uuid=True)),
        sa.column('service_name', sa.String(50)),
        sa.column('name', sa.String(50)),
        sa.column('description', sa.String(200)),
        sa.column('is_active', sa.Boolean)
    )
    
    permissions_table = sa.table(
        'permissions',
        sa.column('id', UNIQUEIDENTIFIER(as_uuid=True)),
        sa.column('service_name', sa.String(50)),
        sa.column('name', sa.String(50)),
        sa.column('resource', sa.String(50)),
        sa.column('action', sa.String(30)),
        sa.column('description', sa.String(200))
    )
    
    role_permissions_table = sa.table(
        'role_permissions',
        sa.column('id', UNIQUEIDENTIFIER(as_uuid=True)),
        sa.column('role_id', UNIQUEIDENTIFIER(as_uuid=True)),
        sa.column('permission_id', UNIQUEIDENTIFIER(as_uuid=True))
    )
    
    users_table = sa.table(
        'users',
        sa.column('id', UNIQUEIDENTIFIER(as_uuid=True)),
        sa.column('first_name', sa.String(50)),
        sa.column('middle_name', sa.String(50)),
        sa.column('last_name', sa.String(50)),
        sa.column('email', sa.String(250)),
        sa.column('hashed_password', sa.String(200)),
        sa.column('is_active', sa.Boolean),
        sa.column('is_verified', sa.Boolean)
    )
    
    user_roles_table = sa.table(
        'user_roles',
        sa.column('id', UNIQUEIDENTIFIER(as_uuid=True)),
        sa.column('user_id', UNIQUEIDENTIFIER(as_uuid=True)),
        sa.column('role_id', UNIQUEIDENTIFIER(as_uuid=True))
    )

    # Service name for this identity service
    SERVICE_NAME = 'identity-service'
    
    # Generate UUIDs for roles
    admin_role_id = uuid.uuid4()
    user_role_id = uuid.uuid4()
    
    # Insert roles
    op.bulk_insert(
        roles_table,
        [
            {
                'id': admin_role_id,
                'service_name': SERVICE_NAME,
                'name': 'admin',
                'description': 'Administrator with full system access',
                'is_active': True
            },
            {
                'id': user_role_id,
                'service_name': SERVICE_NAME,
                'name': 'user',
                'description': 'Standard user with limited access',
                'is_active': True
            }
        ]
    )
    
    # Define permissions with UUIDs
    permissions_data = [
        # User management permissions
        {
            'id': uuid.uuid4(),
            'service_name': SERVICE_NAME,
            'name': 'Create User',
            'resource': 'user',
            'action': 'create',
            'description': 'Permission to create new users'
        },
        {
            'id': uuid.uuid4(),
            'service_name': SERVICE_NAME,
            'name': 'Read User',
            'resource': 'user',
            'action': 'read',
            'description': 'Permission to view user information'
        },
        {
            'id': uuid.uuid4(),
            'service_name': SERVICE_NAME,
            'name': 'Update User',
            'resource': 'user',
            'action': 'update',
            'description': 'Permission to update user information'
        },
        {
            'id': uuid.uuid4(),
            'service_name': SERVICE_NAME,
            'name': 'Delete User',
            'resource': 'user',
            'action': 'delete',
            'description': 'Permission to delete users'
        },
        # Role management permissions
        {
            'id': uuid.uuid4(),
            'service_name': SERVICE_NAME,
            'name': 'Manage Roles',
            'resource': 'role',
            'action': 'manage',
            'description': 'Permission to manage roles'
        },
        {
            'id': uuid.uuid4(),
            'service_name': SERVICE_NAME,
            'name': 'Assign Roles',
            'resource': 'role',
            'action': 'assign',
            'description': 'Permission to assign roles to users'
        },
        # Permission management permissions
        {
            'id': uuid.uuid4(),
            'service_name': SERVICE_NAME,
            'name': 'Manage Permissions',
            'resource': 'permission',
            'action': 'manage',
            'description': 'Permission to manage permissions'
        },
        {
            'id': uuid.uuid4(),
            'service_name': SERVICE_NAME,
            'name': 'Assign Permissions',
            'resource': 'permission',
            'action': 'assign',
            'description': 'Permission to assign permissions to users or roles'
        },
        # Profile permissions
        {
            'id': uuid.uuid4(),
            'service_name': SERVICE_NAME,
            'name': 'Read Own Profile',
            'resource': 'profile',
            'action': 'read',
            'description': 'Permission to view own profile'
        },
        {
            'id': uuid.uuid4(),
            'service_name': SERVICE_NAME,
            'name': 'Update Own Profile',
            'resource': 'profile',
            'action': 'update',
            'description': 'Permission to update own profile'
        },
        # Authentication permissions
        {
            'id': uuid.uuid4(),
            'service_name': SERVICE_NAME,
            'name': 'Refresh Token',
            'resource': 'auth',
            'action': 'refresh',
            'description': 'Permission to refresh authentication tokens'
        }
    ]
    
    # Insert permissions
    op.bulk_insert(permissions_table, permissions_data)
    
    # Assign all permissions to Admin role
    admin_role_permissions = [
        {
            'id': str(uuid.uuid4()),
            'role_id': admin_role_id,
            'permission_id': perm['id']
        }
        for perm in permissions_data
    ]
    
    # Assign limited permissions to User role (profile and auth only)
    user_role_permissions = [
        {
            'id': str(uuid.uuid4()),
            'role_id': user_role_id,
            'permission_id': perm['id']
        }
        for perm in permissions_data
        if perm['resource'] in ('profile', 'auth') or (perm['resource'] == 'user' and perm['action'] == 'read')
    ]
    
    # Insert role-permission mappings
    op.bulk_insert(role_permissions_table, admin_role_permissions)
    op.bulk_insert(role_permissions_table, user_role_permissions)
    
    # Generate UUID for admin user
    admin_user_id = str(uuid.uuid4())
    
    # Insert admin user
    # Password is 'Admin@123' hashed with bcrypt
    # To generate a new hash, use: from passlib.context import CryptContext; CryptContext(schemes=['bcrypt']).hash('your_password')
    op.bulk_insert(
        users_table,
        [
            {
                'id': admin_user_id,
                'first_name': 'System',
                'middle_name': None,
                'last_name': 'Administrator',
                'email': 'admin@email.com',
                'hashed_password': admin_hashed_password,
                'is_active': True,
                'is_verified': True
            }
        ]
    )
    
    # Assign Admin role to admin user
    op.bulk_insert(
        user_roles_table,
        [
            {
                'id': str(uuid.uuid4()),
                'user_id': admin_user_id,
                'role_id': admin_role_id
            }
        ]
    )


def downgrade() -> None:
    """Downgrade schema - remove seed data."""
    # Delete in reverse order due to foreign key constraints
    op.execute("DELETE FROM user_roles WHERE user_id IN (SELECT id FROM users WHERE email = 'admin@identityservice.local')")
    op.execute("DELETE FROM users WHERE email = 'admin@identityservice.local'")
    op.execute("DELETE FROM role_permissions WHERE role_id IN (SELECT id FROM roles WHERE service_name = 'identity-service' AND name IN ('admin', 'user'))")
    op.execute("DELETE FROM permissions WHERE service_name = 'identity-service'")
    op.execute("DELETE FROM roles WHERE service_name = 'identity-service' AND name IN ('admin', 'user')")