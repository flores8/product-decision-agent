"""initial

Revision ID: 197750e12029
Revises: 
Create Date: 2024-02-06 05:05:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision: str = '197750e12029'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Create files table
    op.create_table('files',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('filename', sa.String(), nullable=False),
        sa.Column('mime_type', sa.String(), nullable=True),
        sa.Column('storage_path', sa.String(), nullable=False),
        sa.Column('storage_backend', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create threads table
    op.create_table('threads',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=True),
        sa.Column('attributes', sa.JSON(), nullable=False, server_default='{}'),
        sa.Column('source', sa.JSON(), nullable=True),
        sa.Column('metrics', sa.JSON(), nullable=False, server_default='{}', comment='Thread-level metrics'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create messages table with sequence column
    op.create_table('messages',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('thread_id', sa.String(), nullable=False),
        sa.Column('sequence', sa.Integer(), nullable=False),  # Message order in thread
        sa.Column('role', sa.String(), nullable=False),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('tool_call_id', sa.String(), nullable=True),
        sa.Column('tool_calls', sa.JSON(), nullable=True),
        sa.Column('attributes', sa.JSON(), nullable=False, server_default='{}'),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column('source', sa.JSON(), nullable=True),
        sa.Column('attachments', sa.JSON(), nullable=True),
        sa.Column('metrics', sa.JSON(), nullable=False, server_default='{}', comment='Message-level metrics'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['thread_id'], ['threads.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('thread_id', 'sequence', name='uq_message_thread_sequence')  # Ensure unique sequences per thread
    )
    
    # Add indexes
    op.create_index(op.f('ix_files_filename'), 'files', ['filename'], unique=False)
    op.create_index(op.f('ix_threads_updated_at'), 'threads', ['updated_at'], unique=False)
    op.create_index(op.f('ix_messages_thread_id'), 'messages', ['thread_id'], unique=False)
    op.create_index(op.f('ix_messages_timestamp'), 'messages', ['timestamp'], unique=False)
    op.create_index(op.f('ix_messages_sequence'), 'messages', ['sequence'], unique=False)

def downgrade() -> None:
    op.drop_index(op.f('ix_messages_sequence'), table_name='messages')
    op.drop_index(op.f('ix_messages_timestamp'), table_name='messages')
    op.drop_index(op.f('ix_messages_thread_id'), table_name='messages')
    op.drop_index(op.f('ix_threads_updated_at'), table_name='threads')
    op.drop_index(op.f('ix_files_filename'), table_name='files')
    op.drop_table('messages')
    op.drop_table('threads')
    op.drop_table('files') 