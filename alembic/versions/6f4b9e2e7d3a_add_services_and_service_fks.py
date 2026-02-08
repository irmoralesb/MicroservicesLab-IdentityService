"""add_services_and_service_fks

Revision ID: 6f4b9e2e7d3a
Revises: 44306e914fda
Create Date: 2026-02-07 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6f4b9e2e7d3a'
down_revision: Union[str, Sequence[str], None] = '44306e914fda'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'services',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False,
                  comment='Service name used for RBAC scoping'),
        sa.Column('description', sa.String(length=255), nullable=True,
                  comment='Service description'),
        sa.Column('is_active', sa.Boolean(), nullable=False,
                  server_default=sa.text('1'),
                  comment='Whether this service is active'),
        sa.Column('url', sa.String(length=255), nullable=True,
                  comment='Base URL for the service'),
        sa.Column('port', sa.Integer(), nullable=True,
                  comment='Network port for the service'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('SYSDATETIMEOFFSET()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('SYSDATETIMEOFFSET()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name', name='uix_services_name')
    )
    op.create_index('ix_services_name', 'services', ['name'], unique=False)

    op.add_column('roles', sa.Column('service_id', sa.String(length=36), nullable=True))
    op.add_column('permissions', sa.Column('service_id', sa.String(length=36), nullable=True))

    op.create_foreign_key(
        'fk_roles_service_id', 'roles', 'services',
        ['service_id'], ['id'],
        ondelete='NO ACTION',
        onupdate='NO ACTION'
    )
    op.create_foreign_key(
        'fk_permissions_service_id', 'permissions', 'services',
        ['service_id'], ['id'],
        ondelete='NO ACTION',
        onupdate='NO ACTION'
    )

    op.execute("""
        INSERT INTO services (id, name, description, is_active, url, port, created_at, updated_at)
        SELECT NEWID(), s.service_name, NULL, 1, NULL, NULL, SYSDATETIMEOFFSET(), SYSDATETIMEOFFSET()
        FROM (
            SELECT service_name FROM roles
            UNION
            SELECT service_name FROM permissions
        ) AS s
        WHERE NOT EXISTS (
            SELECT 1 FROM services WHERE services.name = s.service_name
        )
    """)

    op.execute("""
        UPDATE roles
        SET service_id = services.id
        FROM roles
        JOIN services ON services.name = roles.service_name
    """)

    op.execute("""
        UPDATE permissions
        SET service_id = services.id
        FROM permissions
        JOIN services ON services.name = permissions.service_name
    """)

    op.alter_column(
        'roles',
        'service_id',
        existing_type=sa.String(length=36),
        nullable=False
    )
    op.alter_column(
        'permissions',
        'service_id',
        existing_type=sa.String(length=36),
        nullable=False
    )

    op.drop_constraint('uix_service_role_name', 'roles', type_='unique')
    op.drop_index('ix_roles_service_name', table_name='roles')
    op.drop_constraint('uix_service_permission', 'permissions', type_='unique')
    op.drop_index('ix_permission_service_name', table_name='permissions')

    op.drop_column('roles', 'service_name')
    op.drop_column('permissions', 'service_name')

    op.create_unique_constraint('uix_service_role_name', 'roles', ['service_id', 'name'])
    op.create_index('ix_roles_service_id', 'roles', ['service_id'], unique=False)

    op.create_unique_constraint('uix_service_permission', 'permissions', ['service_id', 'resource', 'action'])
    op.create_index('ix_permission_service_id', 'permissions', ['service_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_permission_service_id', table_name='permissions')
    op.drop_constraint('uix_service_permission', 'permissions', type_='unique')
    op.drop_index('ix_roles_service_id', table_name='roles')
    op.drop_constraint('uix_service_role_name', 'roles', type_='unique')

    op.add_column('permissions', sa.Column('service_name', sa.String(length=50), nullable=True))
    op.add_column('roles', sa.Column('service_name', sa.String(length=50), nullable=True))

    op.execute("""
        UPDATE roles
        SET service_name = services.name
        FROM roles
        JOIN services ON services.id = roles.service_id
    """)

    op.execute("""
        UPDATE permissions
        SET service_name = services.name
        FROM permissions
        JOIN services ON services.id = permissions.service_id
    """)

    op.alter_column(
        'roles',
        'service_name',
        existing_type=sa.String(length=50),
        nullable=False
    )
    op.alter_column(
        'permissions',
        'service_name',
        existing_type=sa.String(length=50),
        nullable=False
    )

    op.create_unique_constraint('uix_service_role_name', 'roles', ['service_name', 'name'])
    op.create_index('ix_roles_service_name', 'roles', ['service_name'], unique=False)
    op.create_unique_constraint('uix_service_permission', 'permissions', ['service_name', 'resource', 'action'])
    op.create_index('ix_permission_service_name', 'permissions', ['service_name'], unique=False)

    op.drop_constraint('fk_permissions_service_id', 'permissions', type_='foreignkey')
    op.drop_constraint('fk_roles_service_id', 'roles', type_='foreignkey')
    op.drop_column('permissions', 'service_id')
    op.drop_column('roles', 'service_id')

    op.drop_index('ix_services_name', table_name='services')
    op.drop_table('services')
