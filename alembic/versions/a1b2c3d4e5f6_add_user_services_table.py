"""add_user_services_table

Revision ID: a1b2c3d4e5f6
Revises: f8536bfac7ee
Create Date: 2026-02-16 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'f8536bfac7ee'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create user_services table
    op.create_table(
        'user_services',
        sa.Column('id', UNIQUEIDENTIFIER(as_uuid=True), nullable=False, primary_key=True),
        sa.Column('user_id', UNIQUEIDENTIFIER(as_uuid=True), nullable=False),
        sa.Column('service_id', UNIQUEIDENTIFIER(as_uuid=True), nullable=False),
        sa.Column('assigned_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE', onupdate='NO ACTION'),
        sa.ForeignKeyConstraint(['service_id'], ['services.id'], ondelete='CASCADE', onupdate='NO ACTION'),
        sa.UniqueConstraint('user_id', 'service_id', name='uix_user_service'),
    )
    
    # Create indexes
    op.create_index('ix_user_service_user_id', 'user_services', ['user_id'])
    op.create_index('ix_user_service_service_id', 'user_services', ['service_id'])
    
    # Assign identity-service to users who already have roles for it
    op.execute("""
        INSERT INTO user_services (id, user_id, service_id, assigned_at)
        SELECT DISTINCT
            NEWID(),
            u.id,
            s.id,
            SYSDATETIMEOFFSET()
        FROM users u
        INNER JOIN user_roles ur ON ur.user_id = u.id
        INNER JOIN roles r ON r.id = ur.role_id
        INNER JOIN services s ON s.id = r.service_id
        WHERE s.name = 'identity-service'
        AND NOT EXISTS (
            SELECT 1 FROM user_services us 
            WHERE us.user_id = u.id AND us.service_id = s.id
        )
    """)


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_user_service_service_id', table_name='user_services')
    op.drop_index('ix_user_service_user_id', table_name='user_services')
    
    # Drop table (CASCADE will handle deletion of rows)
    op.drop_table('user_services')
