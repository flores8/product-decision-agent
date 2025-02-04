import pytest
import os
from pathlib import Path
import tempfile
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text, inspect
from tyler.database.thread_store import ThreadStore, ThreadRecord
from tyler.models.thread import Thread
from tyler.models.message import Message

@pytest.fixture
def temp_db():
    """Create a temporary SQLite database for testing."""
    with tempfile.NamedTemporaryFile(suffix='.db') as f:
        url = f"sqlite:///{f.name}"
        yield url

@pytest.fixture
def alembic_config():
    """Get Alembic config for testing."""
    package_dir = Path(__file__).parent.parent.parent / "tyler" / "database"
    alembic_ini = package_dir / "migrations" / "alembic.ini"
    config = Config(alembic_ini)
    return config

def test_initial_migration(temp_db, alembic_config):
    """Test that initial migration creates correct schema."""
    # Set test database URL
    alembic_config.set_main_option("sqlalchemy.url", temp_db)
    
    # Run migrations
    command.upgrade(alembic_config, "head")
    
    # Check schema
    engine = create_engine(temp_db)
    inspector = inspect(engine)
    
    # Check if threads table exists
    assert 'threads' in inspector.get_table_names()
    
    # Check columns
    columns = {col['name']: col for col in inspector.get_columns('threads')}
    assert 'id' in columns
    assert 'data' in columns
    assert 'created_at' in columns
    assert 'updated_at' in columns
    
    # Check column types
    assert columns['id']['type'].__class__.__name__ == 'String'
    assert columns['data']['type'].__class__.__name__ == 'JSON'
    assert columns['created_at']['type'].__class__.__name__ == 'DateTime'
    assert columns['updated_at']['type'].__class__.__name__ == 'DateTime'
    
    # Check indexes
    indexes = inspector.get_indexes('threads')
    index_names = [idx['name'] for idx in indexes]
    assert 'ix_threads_created_at' in index_names
    assert 'ix_threads_updated_at' in index_names

def test_migration_with_data(temp_db, alembic_config):
    """Test that migrations preserve existing data."""
    # Set up database and store
    alembic_config.set_main_option("sqlalchemy.url", temp_db)
    command.upgrade(alembic_config, "head")
    store = ThreadStore(temp_db)
    
    # Add test data with various fields
    thread = Thread()
    thread.title = "Test Thread"
    thread.attributes = {"category": "test", "priority": "high"}
    thread.source = {"name": "test", "id": "123"}
    
    # Add messages
    thread.add_message(Message(role="user", content="Test message"))
    thread.add_message(Message(role="assistant", content="Test response"))
    
    store.save_thread(thread)
    
    # Run a dummy migration (if we add one later)
    # command.upgrade(alembic_config, "head")
    
    # Verify all data is preserved
    retrieved = store.get_thread(thread.id)
    assert retrieved is not None
    assert retrieved.id == thread.id
    assert retrieved.title == thread.title
    assert retrieved.attributes == thread.attributes
    assert retrieved.source == thread.source
    assert len(retrieved.messages) == 2
    assert retrieved.messages[0].role == "user"
    assert retrieved.messages[1].role == "assistant"

def test_migration_downgrade(temp_db, alembic_config):
    """Test that downgrades work correctly."""
    # Set up database
    alembic_config.set_main_option("sqlalchemy.url", temp_db)
    
    # Run migrations up
    command.upgrade(alembic_config, "head")
    
    # Add some data
    store = ThreadStore(temp_db)
    thread = Thread()
    store.save_thread(thread)
    
    # Run migrations down
    command.downgrade(alembic_config, "-1")
    
    # Check that tables and indexes are gone
    engine = create_engine(temp_db)
    inspector = inspect(engine)
    assert 'threads' not in inspector.get_table_names()

def test_migration_idempotency(temp_db, alembic_config):
    """Test that running migrations multiple times is safe."""
    alembic_config.set_main_option("sqlalchemy.url", temp_db)
    
    # Run migrations multiple times
    command.upgrade(alembic_config, "head")
    command.upgrade(alembic_config, "head")
    
    # Should not raise any errors
    engine = create_engine(temp_db)
    inspector = inspect(engine)
    assert 'threads' in inspector.get_table_names()

def test_migration_empty_db(temp_db, alembic_config):
    """Test migrations on empty database."""
    alembic_config.set_main_option("sqlalchemy.url", temp_db)
    
    # Create empty database first
    engine = create_engine(temp_db)
    
    # Run migrations
    command.upgrade(alembic_config, "head")
    
    # Check schema was created
    inspector = inspect(engine)
    assert 'threads' in inspector.get_table_names() 