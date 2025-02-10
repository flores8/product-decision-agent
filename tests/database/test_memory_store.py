import pytest
from tyler.database.memory_store import MemoryThreadStore
from tyler.models.thread import Thread
from tyler.models.message import Message
from datetime import datetime, UTC
import pytest_asyncio
import asyncio

@pytest.fixture
def memory_store():
    """Create a memory store for testing."""
    return MemoryThreadStore()

@pytest.fixture
def sample_thread():
    """Create a sample thread for testing."""
    thread = Thread(id="test-thread", title="Test Thread")
    thread.add_message(Message(role="user", content="Hello"))
    return thread

@pytest.mark.asyncio
async def test_memory_store_save_and_get(memory_store, sample_thread):
    """Test saving and retrieving a thread from memory store."""
    # Save the thread
    await memory_store.save(sample_thread)
    
    # Retrieve the thread
    retrieved = await memory_store.get(sample_thread.id)
    assert retrieved is not None
    assert retrieved.id == sample_thread.id
    assert retrieved.title == sample_thread.title
    assert len(retrieved.messages) == 1
    assert retrieved.messages[0].role == "user"
    assert retrieved.messages[0].content == "Hello"

@pytest.mark.asyncio
async def test_memory_store_get_nonexistent():
    """Test retrieving a nonexistent thread."""
    store = MemoryThreadStore()
    retrieved = await store.get("nonexistent-id")
    assert retrieved is None

@pytest.mark.asyncio
async def test_memory_store_list_recent(memory_store):
    """Test listing recent threads."""
    # Create and save multiple threads
    threads = []
    for i in range(3):
        thread = Thread(
            id=f"test-thread-{i}",
            title=f"Test Thread {i}",
            created_at=datetime.now(UTC)
        )
        thread.add_message(Message(role="user", content=f"Message {i}"))
        await memory_store.save(thread)
        threads.append(thread)
    
    # List recent threads
    recent = await memory_store.list_recent(limit=2)
    assert len(recent) == 2
    # Should be in reverse order (most recent first)
    assert recent[0].id == "test-thread-2"
    assert recent[1].id == "test-thread-1"

@pytest.mark.asyncio
async def test_memory_store_update_existing(memory_store, sample_thread):
    """Test updating an existing thread."""
    # Save initial thread
    await memory_store.save(sample_thread)
    
    # Modify and save again
    sample_thread.title = "Updated Title"
    sample_thread.add_message(Message(role="assistant", content="Response"))
    await memory_store.save(sample_thread)
    
    # Verify updates
    retrieved = await memory_store.get(sample_thread.id)
    assert retrieved.title == "Updated Title"
    assert len(retrieved.messages) == 2
    assert retrieved.messages[1].role == "assistant"
    assert retrieved.messages[1].content == "Response"

@pytest.mark.asyncio
async def test_memory_store_delete(memory_store, sample_thread):
    """Test deleting a thread."""
    # Save the thread
    await memory_store.save(sample_thread)
    
    # Delete the thread
    await memory_store.delete(sample_thread.id)
    
    # Verify it's gone
    retrieved = await memory_store.get(sample_thread.id)
    assert retrieved is None

@pytest.mark.asyncio
async def test_memory_store_list_empty():
    """Test listing threads when store is empty."""
    store = MemoryThreadStore()
    threads = await store.list_recent()
    assert len(threads) == 0

@pytest.mark.asyncio
async def test_memory_store_save_with_attributes(memory_store):
    """Test saving thread with various attributes."""
    thread = Thread(
        id="test-thread",
        title="Test Thread",
        attributes={"category": "test", "priority": "high"},
        source={"name": "test", "id": "123"}
    )
    thread.add_message(Message(
        role="user",
        content="Test message",
        attributes={"sentiment": "positive"}
    ))
    
    await memory_store.save(thread)
    retrieved = await memory_store.get(thread.id)
    
    assert retrieved.attributes == {"category": "test", "priority": "high"}
    assert retrieved.source == {"name": "test", "id": "123"}
    assert retrieved.messages[0].attributes == {"sentiment": "positive"}

@pytest.mark.asyncio
async def test_memory_store_concurrent_access(memory_store, sample_thread):
    """Test concurrent access to memory store."""
    # Save initial thread
    await memory_store.save(sample_thread)
    
    # Simulate concurrent updates
    async def update_thread():
        thread = await memory_store.get(sample_thread.id)
        thread.add_message(Message(role="user", content="Concurrent update"))
        await memory_store.save(thread)
    
    # Run multiple updates concurrently
    await asyncio.gather(*[update_thread() for _ in range(3)])
    
    # Verify final state
    retrieved = await memory_store.get(sample_thread.id)
    assert len(retrieved.messages) == 4  # Original + 3 concurrent updates 