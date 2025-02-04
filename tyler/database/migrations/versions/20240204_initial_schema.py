"""Initial schema

Revision ID: 20240204_initial
Create Date: 2024-02-04 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic
revision = '20240204_initial'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Create threads table
    op.create_table(
        'threads',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('data', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Add indexes for performance
    op.create_index(
        'ix_threads_created_at',
        'threads',
        ['created_at'],
        unique=False
    )
    op.create_index(
        'ix_threads_updated_at',
        'threads',
        ['updated_at'],
        unique=False
    )

def downgrade() -> None:
    # Remove indexes
    op.drop_index('ix_threads_updated_at', table_name='threads')
    op.drop_index('ix_threads_created_at', table_name='threads')
    
    # Drop threads table
    op.drop_table('threads') 