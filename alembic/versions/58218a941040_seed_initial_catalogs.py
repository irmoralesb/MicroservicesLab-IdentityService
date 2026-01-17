"""seed_initial_catalogs

Revision ID: 58218a941040
Revises: c32e96993dd9
Create Date: 2026-01-16 22:34:12.576242

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import uuid

# revision identifiers, used by Alembic.
revision: str = '58218a941040'
down_revision: Union[str, Sequence[str], None] = 'c32e96993dd9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - insert seed data."""
    # Create table references
    roles_table = sa.table(
        'roles',
        sa.column('id', sa.String(36)),
        sa.column('name', sa.String(30)),
        sa.column('description', sa.String(200))
    )
    
    permissions_table = sa.table(
        'permissions',
        sa.column('id', sa.String(36)),
        sa.column('name', sa.String(30)),
        sa.column('resource', sa.String(30)),
        sa.column('action', sa.String(30))
    )
    
    role_permissions_table = sa.table(
        'role_permissions',
        sa.column('id', sa.String(36)),
        sa.column('role_id', sa.String(36)),
        sa.column('permission_id', sa.String(36))
    )
    

    # Generate UUIDs for roles
    admin_role_id = str(uuid.uuid4())
    user_role_id = str(uuid.uuid4())
    
    # Check if roles already exist
    conn = op.get_bind()
    result = conn.execute(sa.text("SELECT COUNT(*) FROM roles WHERE name IN ('Admin', 'User')"))
    if (result.scalar() or 0) > 0:
        return  # Data already seeded
    
    # Insert roles
    op.bulk_insert(
        roles_table,
        [
            {
                'id': admin_role_id,
                'name': 'Admin',
                'description': 'Administrator with full system access'
            },
            {
                'id': user_role_id,
                'name': 'User',
                'description': 'Standard user with limited access'
            }
        ]
    )
    
    # Define permissions with UUIDs
    permissions_data = [
        # User management permissions
        {
            'id': str(uuid.uuid4()),
            'name': 'create_user',
            'resource': 'users',
            'action': 'create'
        },
        {
            'id': str(uuid.uuid4()),
            'name': 'read_user',
            'resource': 'users',
            'action': 'read'
        },
        {
            'id': str(uuid.uuid4()),
            'name': 'update_user',
            'resource': 'users',
            'action': 'update'
        },
        {
            'id': str(uuid.uuid4()),
            'name': 'delete_user',
            'resource': 'users',
            'action': 'delete'
        },
        # Role management permissions
        {
            'id': str(uuid.uuid4()),
            'name': 'manage_roles',
            'resource': 'roles',
            'action': 'manage'
        },
        # Permission management permissions
        {
            'id': str(uuid.uuid4()),
            'name': 'manage_permissions',
            'resource': 'permissions',
            'action': 'manage'
        },
        # Profile permissions
        {
            'id': str(uuid.uuid4()),
            'name': 'read_own_profile',
            'resource': 'profile',
            'action': 'read'
        },
        {
            'id': str(uuid.uuid4()),
            'name': 'update_own_profile',
            'resource': 'profile',
            'action': 'update'
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
    
    # Assign limited permissions to User role (only profile-related)
    user_role_permissions = [
        {
            'id': str(uuid.uuid4()),
            'role_id': user_role_id,
            'permission_id': perm['id']
        }
        for perm in permissions_data
        if perm['resource'] == 'profile' or (perm['resource'] == 'users' and perm['action'] == 'read')
    ]
    
    # Insert role-permission mappings
    op.bulk_insert(role_permissions_table, admin_role_permissions)
    op.bulk_insert(role_permissions_table, user_role_permissions)
    


def downgrade() -> None:
    """Downgrade schema - remove seed data."""
    # Delete in reverse order due to foreign key constraints
    op.execute("DELETE FROM role_permissions WHERE role_id IN (SELECT id FROM roles WHERE name IN ('Admin', 'User'))")
    op.execute("DELETE FROM permissions WHERE resource IN ('users', 'roles', 'permissions', 'profile')")
    op.execute("DELETE FROM roles WHERE name IN ('Admin', 'User')")