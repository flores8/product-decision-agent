"""initial

Revision ID: 197750e12029
Revises: 
Create Date: 2025-02-06 05:05:58.448173+00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic
revision = '197750e12029'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create the threads table with proper schema
    op.create_table(
        'threads',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('data', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), 
                 server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True),
                 server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('threads') 