"""add_service_and_role_permissions

Revision ID: f2dcdd30b0f5
Revises: 6f4b9e2e7d3a
Create Date: 2026-02-09 21:32:57.984243

"""
from typing import Sequence, Union
import uuid

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER


# revision identifiers, used by Alembic.
revision: str = 'f2dcdd30b0f5'
down_revision: Union[str, Sequence[str], None] = '6f4b9e2e7d3a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add service and role CRUD permissions and assign to admin role."""
    # Get database connection
    conn = op.get_bind()
    
    # Get the identity-service service_id
    SERVICE_NAME = 'identity-service'
    result = conn.execute(
        sa.text("SELECT id FROM services WHERE name = :service_name"),
        {"service_name": SERVICE_NAME}
    )
    service_row = result.fetchone()
    
    if not service_row:
        raise Exception(f"Service '{SERVICE_NAME}' not found in services table")
    
    service_id = service_row[0]
    
    # Create table references
    permissions_table = sa.table(
        'permissions',
        sa.column('id', UNIQUEIDENTIFIER(as_uuid=True)),
        sa.column('service_id', sa.String(36)),
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
    
    # Define new permissions with UUIDs
    permissions_data = [
        # Service management permissions
        {
            'id': uuid.uuid4(),
            'service_id': service_id,
            'name': 'Create Service',
            'resource': 'service',
            'action': 'create',
            'description': 'Permission to create new services'
        },
        {
            'id': uuid.uuid4(),
            'service_id': service_id,
            'name': 'Update Service',
            'resource': 'service',
            'action': 'update',
            'description': 'Permission to update service information'
        },
        {
            'id': uuid.uuid4(),
            'service_id': service_id,
            'name': 'Delete Service',
            'resource': 'service',
            'action': 'delete',
            'description': 'Permission to delete services'
        },
        {
            'id': uuid.uuid4(),
            'service_id': service_id,
            'name': 'Read Service',
            'resource': 'service',
            'action': 'read',
            'description': 'Permission to view service information'
        },
        # Role CRUD permissions (replacing the old "Manage Roles" permission)
        {
            'id': uuid.uuid4(),
            'service_id': service_id,
            'name': 'Create Role',
            'resource': 'role',
            'action': 'create',
            'description': 'Permission to create new roles'
        },
        {
            'id': uuid.uuid4(),
            'service_id': service_id,
            'name': 'Update Role',
            'resource': 'role',
            'action': 'update',
            'description': 'Permission to update role information'
        },
        {
            'id': uuid.uuid4(),
            'service_id': service_id,
            'name': 'Delete Role',
            'resource': 'role',
            'action': 'delete',
            'description': 'Permission to delete roles'
        },
        {
            'id': uuid.uuid4(),
            'service_id': service_id,
            'name': 'Read Role',
            'resource': 'role',
            'action': 'read',
            'description': 'Permission to view role information'
        }
    ]
    
    # Insert permissions
    op.bulk_insert(permissions_table, permissions_data)
    
    # Get admin role ID from database
    result = conn.execute(
        sa.text(
            "SELECT id FROM roles WHERE service_id = :service_id AND name = :role_name"
        ),
        {"service_id": service_id, "role_name": "admin"}
    )
    admin_role = result.fetchone()
    
    if admin_role:
        admin_role_id = admin_role[0]
        
        # Assign all new permissions to Admin role
        admin_role_permissions = [
            {
                'id': uuid.uuid4(),
                'role_id': admin_role_id,
                'permission_id': perm['id']
            }
            for perm in permissions_data
        ]
        
        # Insert role-permission mappings
        op.bulk_insert(role_permissions_table, admin_role_permissions)


def downgrade() -> None:
    """Remove service and role CRUD permissions."""
    # Get database connection
    conn = op.get_bind()
    
    # Get the identity-service service_id
    SERVICE_NAME = 'identity-service'
    result = conn.execute(
        sa.text("SELECT id FROM services WHERE name = :service_name"),
        {"service_name": SERVICE_NAME}
    )
    service_row = result.fetchone()
    
    if service_row:
        service_id = service_row[0]
        
        # Delete role-permission mappings for these permissions
        op.execute(
            sa.text("""
                DELETE FROM role_permissions 
                WHERE permission_id IN (
                    SELECT id FROM permissions 
                    WHERE service_id = :service_id 
                    AND resource IN ('service', 'role')
                    AND action IN ('create', 'read', 'update', 'delete')
                )
            """),
            {"service_id": service_id}
        )
        
        # Delete the permissions
        op.execute(
            sa.text("""
                DELETE FROM permissions 
                WHERE service_id = :service_id 
                AND resource IN ('service', 'role')
                AND action IN ('create', 'read', 'update', 'delete')
            """),
            {"service_id": service_id}
        )
