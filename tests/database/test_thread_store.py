import pytest
import os
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from tyler.database.thread_store import ThreadStore, ThreadRecord, Base
from tyler.models.thread import Thread
from tyler.models.message import Message

@pytest.fixture
def env_vars():
    """Save and restore environment variables."""
    old_vars = {}
    for var in [
        "TYLER_DB_TYPE",
        "TYLER_DB_HOST",
        "TYLER_DB_PORT",
        "TYLER_DB_NAME",
        "TYLER_DB_USER",
        "TYLER_DB_PASSWORD",
        "TYLER_DB_ECHO",
        "TYLER_DB_POOL_SIZE",
        "TYLER_DB_MAX_OVERFLOW"
    ]:
        old_vars[var] = os.environ.get(var)
    yield
    # Restore old values
    for var, value in old_vars.items():
        if value is None:
            os.environ.pop(var, None)
        else:
            os.environ[var] = value

def test_env_var_config(env_vars):
    """Test ThreadStore initialization with environment variables."""
    # Set environment variables
    os.environ.update({
        "TYLER_DB_TYPE": "sqlite",
        "TYLER_DB_HOST": "testhost",
        "TYLER_DB_PORT": "5433",
        "TYLER_DB_NAME": "testdb",
        "TYLER_DB_USER": "testuser",
        "TYLER_DB_PASSWORD": "testpass",
        "TYLER_DB_ECHO": "true",
        "TYLER_DB_POOL_SIZE": "3",
        "TYLER_DB_MAX_OVERFLOW": "5"
    })
    
    # Initialize store without URL
    store = ThreadStore()
    
    # Verify SQLite URL was constructed correctly
    assert "sqlite" in store.database_url
    assert store.engine.echo is True
    assert store.engine.pool.size() == 3
    assert store.engine.pool._max_overflow == 5

def test_url_override(env_vars):
    """Test that explicit URL overrides environment variables."""
    # Set environment variables
    os.environ.update({
        "TYLER_DB_TYPE": "postgresql",
        "TYLER_DB_HOST": "wronghost",
        "TYLER_DB_PORT": "5432",
        "TYLER_DB_NAME": "wrongdb",
        "TYLER_DB_USER": "wronguser",
        "TYLER_DB_PASSWORD": "wrongpass"
    })
    
    # Initialize with explicit URL
    test_url = "sqlite:///test.db"
    store = ThreadStore(test_url)
    
    # Verify explicit URL was used
    assert store.database_url == test_url

@pytest.fixture
def thread_store():
    """Create a test thread store with in-memory SQLite database"""
    store = ThreadStore(":memory:")  # Use in-memory SQLite for testing
    yield store
    # Cleanup
    store.engine.dispose()

@pytest.fixture
def sample_thread():
    """Create a sample thread for testing"""
    thread = Thread(
        id="test-thread-1",
        title="Test Thread"
    )
    # Add a test message
    message = Message(
        role="user",
        content="Test message"
    )
    thread.add_message(message)
    return thread

def test_thread_store_init():
    """Test ThreadStore initialization"""
    store = ThreadStore(":memory:")
    assert store.engine is not None
    assert store.Session is not None

def test_save_thread(thread_store, sample_thread):
    """Test saving a thread"""
    # Save the thread
    thread_store.save(sample_thread)
    
    # Verify it was saved correctly
    session = thread_store.Session()
    record = session.query(ThreadRecord).get(sample_thread.id)
    assert record is not None
    assert record.data == sample_thread.to_dict()
    session.close()

def test_get_thread(thread_store, sample_thread):
    """Test retrieving a thread"""
    # Save the thread first
    thread_store.save(sample_thread)
    
    # Retrieve the thread
    retrieved_thread = thread_store.get(sample_thread.id)
    assert retrieved_thread is not None
    assert retrieved_thread.id == sample_thread.id
    assert retrieved_thread.title == sample_thread.title
    assert len(retrieved_thread.messages) == 1
    assert retrieved_thread.messages[0].role == "user"
    assert retrieved_thread.messages[0].content == "Test message"

def test_get_nonexistent_thread(thread_store):
    """Test retrieving a non-existent thread"""
    thread = thread_store.get("nonexistent-id")
    assert thread is None

def test_list_recent(thread_store):
    """Test listing recent threads"""
    # Create and save multiple threads
    threads = []
    for i in range(3):
        thread = Thread(
            id=f"test-thread-{i}",
            title=f"Test Thread {i}"
        )
        thread.add_message(Message(role="user", content=f"Message {i}"))
        thread_store.save(thread)
        threads.append(thread)
    
    # List recent threads
    recent_threads = thread_store.list_recent(limit=2)
    assert len(recent_threads) == 2
    # Should be in reverse order (most recent first)
    assert recent_threads[0].id == "test-thread-2"
    assert recent_threads[1].id == "test-thread-1"

def test_delete_thread(thread_store, sample_thread):
    """Test deleting a thread"""
    # Save the thread first
    thread_store.save(sample_thread)
    
    # Delete the thread
    success = thread_store.delete(sample_thread.id)
    assert success is True
    
    # Verify it's gone
    session = thread_store.Session()
    record = session.query(ThreadRecord).get(sample_thread.id)
    assert record is None
    session.close()

def test_delete_nonexistent_thread(thread_store):
    """Test deleting a non-existent thread"""
    success = thread_store.delete("nonexistent-id")
    assert success is False

def test_find_by_attributes(thread_store):
    """Test finding threads by attributes"""
    # Create threads with different attributes
    thread1 = Thread(id="thread-1", title="Thread 1")
    thread1.attributes = {"category": "work", "priority": "high"}
    thread_store.save(thread1)
    
    thread2 = Thread(id="thread-2", title="Thread 2")
    thread2.attributes = {"category": "personal", "priority": "low"}
    thread_store.save(thread2)
    
    # Search by attributes
    results = thread_store.find_by_attributes({"category": "work"})
    assert len(results) == 1
    assert results[0].id == "thread-1"
    
    # Search with multiple attributes
    results = thread_store.find_by_attributes({"category": "personal", "priority": "low"})
    assert len(results) == 1
    assert results[0].id == "thread-2"
    
    # Search with non-matching attributes
    results = thread_store.find_by_attributes({"category": "nonexistent"})
    assert len(results) == 0

def test_find_by_source(thread_store):
    """Test finding threads by source"""
    # Create threads with different sources
    thread1 = Thread(id="thread-1", title="Thread 1")
    thread1.source = {"name": "slack", "channel": "general"}
    thread_store.save(thread1)
    
    thread2 = Thread(id="thread-2", title="Thread 2")
    thread2.source = {"name": "notion", "page_id": "123"}
    thread_store.save(thread2)
    
    # Search by source name and properties
    results = thread_store.find_by_source("slack", {"channel": "general"})
    assert len(results) == 1
    assert results[0].id == "thread-1"
    
    # Search with non-matching source
    results = thread_store.find_by_source("slack", {"channel": "nonexistent"})
    assert len(results) == 0
    
    # Search with non-matching source name
    results = thread_store.find_by_source("nonexistent", {})
    assert len(results) == 0

def test_thread_update(thread_store, sample_thread):
    """Test updating an existing thread"""
    # Save the initial thread
    thread_store.save(sample_thread)
    
    # Modify the thread
    sample_thread.title = "Updated Title"
    sample_thread.add_message(Message(role="assistant", content="Response"))
    
    # Save the updates
    thread_store.save(sample_thread)
    
    # Verify the updates
    updated_thread = thread_store.get(sample_thread.id)
    assert updated_thread.title == "Updated Title"
    assert len(updated_thread.messages) == 2
    assert updated_thread.messages[1].role == "assistant"
    assert updated_thread.messages[1].content == "Response"

def test_thread_store_default_url():
    """Test ThreadStore initialization with default URL."""
    store = ThreadStore()
    assert store.database_url.startswith("sqlite:///")
    assert "tyler_threads" in store.database_url

def test_thread_store_temp_cleanup(tmp_path):
    """Test that temporary database files are cleaned up."""
    # Create store with temp directory
    store = ThreadStore()
    db_path = store.database_url.replace("sqlite:///", "")
    
    # Save a thread
    thread = Thread()
    store.save_thread(thread)
    
    # Verify file exists
    assert os.path.exists(db_path)
    
    # Close connections
    store.engine.dispose()
    
    # File should still exist (persists until program exit)
    assert os.path.exists(db_path)

def test_thread_store_connection_management():
    """Test proper connection management."""
    store = ThreadStore(":memory:")
    
    # Create and save multiple threads
    threads = []
    for i in range(5):
        thread = Thread()
        store.save_thread(thread)
        threads.append(thread)
    
    # Verify all threads can be retrieved
    for thread in threads:
        retrieved = store.get_thread(thread.id)
        assert retrieved is not None
        assert retrieved.id == thread.id
    
    # Close all connections
    store.engine.dispose()

def test_thread_store_concurrent_access():
    """Test concurrent access to thread store."""
    store = ThreadStore(":memory:")
    thread = Thread()
    store.save_thread(thread)
    
    # Simulate concurrent access
    def update_thread():
        # Each operation should get its own session
        retrieved = store.get_thread(thread.id)
        retrieved.title = "Updated"
        store.save_thread(retrieved)
    
    # Run multiple updates
    for _ in range(5):
        update_thread()
    
    # Verify final state
    final = store.get_thread(thread.id)
    assert final.title == "Updated"

def test_thread_store_json_serialization():
    """Test JSON serialization of complex thread data."""
    store = ThreadStore(":memory:")
    thread = Thread()
    
    # Add complex data
    thread.attributes = {
        "nested": {"key": "value"},
        "list": [1, 2, 3],
        "null": None,
        "bool": True
    }
    
    # Save and retrieve
    store.save_thread(thread)
    retrieved = store.get_thread(thread.id)
    
    # Verify complex data is preserved
    assert retrieved.attributes == thread.attributes

def test_thread_store_error_handling():
    """Test error handling in thread store operations."""
    store = ThreadStore(":memory:")
    
    # Test invalid thread ID
    assert store.get_thread("nonexistent") is None
    
    # Test invalid JSON data
    thread = Thread()
    thread.attributes = {"invalid": object()}  # Object that can't be JSON serialized
    
    with pytest.raises(Exception):
        store.save_thread(thread)

def test_thread_store_pagination():
    """Test thread listing with pagination."""
    store = ThreadStore(":memory:")
    
    # Create 15 threads
    threads = []
    for i in range(15):
        thread = Thread()
        thread.title = f"Thread {i}"
        store.save_thread(thread)
        threads.append(thread)
    
    # Test different page sizes
    assert len(store.list_threads(limit=5)) == 5
    assert len(store.list_threads(limit=10, offset=5)) == 10
    assert len(store.list_threads(limit=20)) == 15  # Should return all threads
    
    # Test ordering
    recent = store.list_threads(limit=5)
    assert recent[0].title == "Thread 14"  # Most recent first 