import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.thread_store import ThreadStore, ThreadRecord, Base
from models.thread import Thread
from models.message import Message

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
    thread_id = thread_store.save(sample_thread)
    assert thread_id == sample_thread.id
    
    # Verify it was saved correctly
    session = thread_store.Session()
    record = session.query(ThreadRecord).get(thread_id)
    assert record is not None
    assert record.title == sample_thread.title
    assert len(record.messages) == 1
    assert record.messages[0]["role"] == "user"
    assert record.messages[0]["content"] == "Test message"
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