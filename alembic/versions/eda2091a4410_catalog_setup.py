"""add_admin_service_and_seed_roles_permissions

Revision ID: 6e2b1c3a9f01
Revises: eda2091a44f9
Create Date: 2026-02-05 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
import uuid

# revision identifiers, used by Alembic.
revision: str = '6e2b1c3a9f01'
down_revision: Union[str, Sequence[str], None] = 'eda2091a44f9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    """Add admin_service and seed roles/permissions."""
    # 1. Insert the new service
    service_id = str(uuid.uuid4())
    op.bulk_insert(
        sa.table(
            'services',
            sa.column('id', sa.String(36)),
            sa.column('name', sa.String(100)),
            sa.column('description', sa.String(255)),
            sa.column('url', sa.String(255)),
            sa.column('port', sa.Integer)
        ),
        [{
            'id': service_id,
            'name': 'admin_service',
            'description': 'Admin service',
            'url': 'localhost',
            'port': 8001
        }]
    )

    # 2. Insert roles
    admin_role_id = str(uuid.uuid4())
    user_role_id = str(uuid.uuid4())
    op.bulk_insert(
        sa.table(
            'roles',
            sa.column('id', sa.String(36)),
            sa.column('service_id', sa.String(36)),
            sa.column('name', sa.String(50)),
            sa.column('description', sa.String(200)),
            sa.column('is_active', sa.Boolean)
        ),
        [
            {
                'id': admin_role_id,
                'service_id': service_id,
                'name': 'admin',
                'description': 'Administrator with full system access',
                'is_active': True
            },
            {
                'id': user_role_id,
                'service_id': service_id,
                'name': 'user',
                'description': 'Standard user with limited access',
                'is_active': True
            }
        ]
    )

    # 3. Insert permissions
    permissions_data = [
        {
            'id': str(uuid.uuid4()),
            'service_id': service_id,
            'name': 'Create User',
            'resource': 'user',
            'action': 'create',
            'description': 'Permission to create new users'
        },
        {
            'id': str(uuid.uuid4()),
            'service_id': service_id,
            'name': 'Read User',
            'resource': 'user',
            'action': 'read',
            'description': 'Permission to view user information'
        },
        {
            'id': str(uuid.uuid4()),
            'service_id': service_id,
            'name': 'Update User',
            'resource': 'user',
            'action': 'update',
            'description': 'Permission to update user information'
        },
        {
            'id': str(uuid.uuid4()),
            'service_id': service_id,
            'name': 'Delete User',
            'resource': 'user',
            'action': 'delete',
            'description': 'Permission to delete users'
        },
        {
            'id': str(uuid.uuid4()),
            'service_id': service_id,
            'name': 'Manage Roles',
            'resource': 'role',
            'action': 'manage',
            'description': 'Permission to manage roles'
        },
        {
            'id': str(uuid.uuid4()),
            'service_id': service_id,
            'name': 'Assign Roles',
            'resource': 'role',
            'action': 'assign',
            'description': 'Permission to assign roles to users'
        },
        {
            'id': str(uuid.uuid4()),
            'service_id': service_id,
            'name': 'Manage Permissions',
            'resource': 'permission',
            'action': 'manage',
            'description': 'Permission to manage permissions'
        },
        {
            'id': str(uuid.uuid4()),
            'service_id': service_id,
            'name': 'Assign Permissions',
            'resource': 'permission',
            'action': 'assign',
            'description': 'Permission to assign permissions to users or roles'
        },
        {
            'id': str(uuid.uuid4()),
            'service_id': service_id,
            'name': 'Read Own Profile',
            'resource': 'profile',
            'action': 'read',
            'description': 'Permission to view own profile'
        },
        {
            'id': str(uuid.uuid4()),
            'service_id': service_id,
            'name': 'Update Own Profile',
            'resource': 'profile',
            'action': 'update',
            'description': 'Permission to update own profile'
        },
        {
            'id': str(uuid.uuid4()),
            'service_id': service_id,
            'name': 'Refresh Token',
            'resource': 'auth',
            'action': 'refresh',
            'description': 'Permission to refresh authentication tokens'
        }
    ]
    op.bulk_insert(
        sa.table(
            'permissions',
            sa.column('id', sa.String(36)),
            sa.column('service_id', sa.String(36)),
            sa.column('name', sa.String(50)),
            sa.column('resource', sa.String(50)),
            sa.column('action', sa.String(30)),
            sa.column('description', sa.String(200))
        ),
        permissions_data
    )

    # 4. Insert role-permission mappings
    role_permissions_table = sa.table(
        'role_permissions',
        sa.column('id', sa.String(36)),
        sa.column('role_id', sa.String(36)),
        sa.column('permission_id', sa.String(36))
    )
    admin_role_permissions = [
        {
            'id': str(uuid.uuid4()),
            'role_id': admin_role_id,
            'permission_id': perm['id']
        }
        for perm in permissions_data
    ]
    user_role_permissions = [
        {
            'id': str(uuid.uuid4()),
            'role_id': user_role_id,
            'permission_id': perm['id']
        }
        for perm in permissions_data
        if perm['resource'] in ('profile', 'auth') or (perm['resource'] == 'user' and perm['action'] == 'read')
    ]
    op.bulk_insert(role_permissions_table, admin_role_permissions)
    op.bulk_insert(role_permissions_table, user_role_permissions)

def downgrade() -> None:
    """Remove seeded admin_service, roles, permissions, and mappings."""
    # Remove by service name
    conn = op.get_bind()
    service = conn.execute(sa.text("SELECT id FROM services WHERE name = 'admin_service'"))
    service_id_row = service.first()
    if service_id_row:
        service_id = service_id_row[0]
        conn.execute(sa.text("DELETE FROM role_permissions WHERE role_id IN (SELECT id FROM roles WHERE service_id = :sid)"), {'sid': service_id})
        conn.execute(sa.text("DELETE FROM permissions WHERE service_id = :sid"), {'sid': service_id})
        conn.execute(sa.text("DELETE FROM roles WHERE service_id = :sid"), {'sid': service_id})
        conn.execute(sa.text("DELETE FROM services WHERE id = :sid"), {'sid': service_id})
