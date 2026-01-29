"""add_password_lockout_fields

Revision ID: 420c5c1e5c97
Revises: 58218a941040
Create Date: 2026-01-28 21:08:02.667719

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '420c5c1e5c97'
down_revision: Union[str, Sequence[str], None] = '58218a941040'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add failed_login_attempts column with default value of 0
    op.add_column('users', 
        sa.Column('failed_login_attempts', sa.Integer(), nullable=False, server_default='0',
                  comment='Number of consecutive failed login attempts')
    )
    
    # Add locked_until column (nullable as accounts are unlocked by default)
    op.add_column('users',
        sa.Column('locked_until', sa.DateTime(), nullable=True,
                  comment='Timestamp until which the account is locked')
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Remove the added columns
    op.drop_column('users', 'locked_until')
    op.drop_column('users', 'failed_login_attempts')
