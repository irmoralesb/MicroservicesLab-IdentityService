"""make_datetime_columns_timezone_aware

Revision ID: 084ad1df0af4
Revises: 420c5c1e5c97
Create Date: 2026-01-28 22:14:06.209082

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '084ad1df0af4'
down_revision: Union[str, Sequence[str], None] = '420c5c1e5c97'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # SQL Server: Convert DateTime to DateTimeOffset for timezone support
    # Need to drop and recreate default constraints
    
    # 1. Drop default constraints for created_at and updated_at
    op.execute("""
        DECLARE @ConstraintName nvarchar(200)
        SELECT @ConstraintName = Name 
        FROM sys.default_constraints 
        WHERE parent_object_id = OBJECT_ID('users') 
        AND parent_column_id = (SELECT column_id FROM sys.columns 
                               WHERE object_id = OBJECT_ID('users') 
                               AND name = 'created_at')
        IF @ConstraintName IS NOT NULL
            EXEC('ALTER TABLE users DROP CONSTRAINT ' + @ConstraintName)
    """)
    
    op.execute("""
        DECLARE @ConstraintName nvarchar(200)
        SELECT @ConstraintName = Name 
        FROM sys.default_constraints 
        WHERE parent_object_id = OBJECT_ID('users') 
        AND parent_column_id = (SELECT column_id FROM sys.columns 
                               WHERE object_id = OBJECT_ID('users') 
                               AND name = 'updated_at')
        IF @ConstraintName IS NOT NULL
            EXEC('ALTER TABLE users DROP CONSTRAINT ' + @ConstraintName)
    """)
    
    # 2. Alter columns to DATETIMEOFFSET
    op.execute("""
        ALTER TABLE users 
        ALTER COLUMN locked_until DATETIMEOFFSET(7) NULL;
    """)
    
    op.execute("""
        ALTER TABLE users 
        ALTER COLUMN created_at DATETIMEOFFSET(7) NOT NULL;
    """)
    
    op.execute("""
        ALTER TABLE users 
        ALTER COLUMN updated_at DATETIMEOFFSET(7) NOT NULL;
    """)
    
    # 3. Recreate default constraints using SYSDATETIMEOFFSET()
    op.execute("""
        ALTER TABLE users 
        ADD CONSTRAINT DF_users_created_at DEFAULT SYSDATETIMEOFFSET() FOR created_at;
    """)
    
    op.execute("""
        ALTER TABLE users 
        ADD CONSTRAINT DF_users_updated_at DEFAULT SYSDATETIMEOFFSET() FOR updated_at;
    """)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop timezone-aware default constraints
    op.execute("""
        ALTER TABLE users DROP CONSTRAINT IF EXISTS DF_users_created_at;
    """)
    
    op.execute("""
        ALTER TABLE users DROP CONSTRAINT IF EXISTS DF_users_updated_at;
    """)
    
    # Convert back to DateTime (will lose timezone info)
    op.execute("""
        ALTER TABLE users 
        ALTER COLUMN locked_until DATETIME NULL;
    """)
    
    op.execute("""
        ALTER TABLE users 
        ALTER COLUMN created_at DATETIME NOT NULL;
    """)
    
    op.execute("""
        ALTER TABLE users 
        ALTER COLUMN updated_at DATETIME NOT NULL;
    """)
    
    # Recreate original default constraints
    op.execute("""
        ALTER TABLE users 
        ADD DEFAULT GETUTCDATE() FOR created_at;
    """)
    
    op.execute("""
        ALTER TABLE users 
        ADD DEFAULT GETUTCDATE() FOR updated_at;
    """)
