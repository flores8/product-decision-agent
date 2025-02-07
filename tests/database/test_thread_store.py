import pytest
import os
from pathlib import Path
import tempfile
from datetime import datetime, UTC
from sqlalchemy import select, text
from sqlalchemy.orm import selectinload
from tyler.database.thread_store import ThreadStore, ThreadRecord
from tyler.models.thread import Thread
from tyler.models.message import Message
from tyler.database.models import Base
from sqlalchemy.ext.asyncio import greenlet_spawn

pytest_plugins = ('pytest_asyncio',)

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

@pytest.mark.asyncio
async def test_env_var_config(env_vars):
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
    assert "sqlite+aiosqlite" in store.database_url
    assert store.engine.echo is True

@pytest.mark.asyncio
async def test_url_override(env_vars):
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
    test_url = "sqlite+aiosqlite:///test.db"
    store = ThreadStore(test_url)
    
    # Verify explicit URL was used
    assert store.database_url == test_url

@pytest.fixture
async def thread_store():
    """Create a thread store for testing."""
    store = ThreadStore()
    
    # Create tables
    async with store.engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    yield store
    
    # Cleanup
    await store.engine.dispose()
    async with store.engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
def sample_thread():
    """Create a sample thread for testing."""
    thread = Thread(id="test-thread-1", title="Test Thread")
    thread.add_message(Message(role="user", content="Hello"))
    thread.updated_at = datetime.now(UTC)
    return thread

@pytest.mark.asyncio
async def test_thread_store_init():
    """Test ThreadStore initialization"""
    store = ThreadStore("sqlite+aiosqlite:///:memory:")
    assert store.engine is not None
    assert store.async_session is not None

@pytest.mark.asyncio
async def test_save_thread(thread_store, sample_thread):
    """Test saving a thread"""
    # Save the thread
    await thread_store.save(sample_thread)
    
    # Verify it was saved correctly
    async with thread_store.async_session() as session:
        async with session.begin():
            def get_thread():
                return session.get(ThreadRecord, sample_thread.id, options=[selectinload(ThreadRecord.messages)])
            
            record = await greenlet_spawn(get_thread)
            assert record is not None
            assert record.title == sample_thread.title
            assert record.attributes == {}
            assert len(record.messages) == 1
            assert record.messages[0].role == "user"
            assert record.messages[0].content == "Hello"

@pytest.mark.asyncio
async def test_get_thread(thread_store, sample_thread):
    """Test retrieving a thread"""
    # Save the thread first
    await thread_store.save(sample_thread)
    
    # Retrieve the thread
    retrieved_thread = await thread_store.get(sample_thread.id)
    assert retrieved_thread is not None
    assert retrieved_thread.id == sample_thread.id
    assert retrieved_thread.title == sample_thread.title
    assert len(retrieved_thread.messages) == 1
    assert retrieved_thread.messages[0].role == "user"
    assert retrieved_thread.messages[0].content == "Hello"

@pytest.mark.asyncio
async def test_get_nonexistent_thread(thread_store):
    """Test retrieving a non-existent thread"""
    thread = await thread_store.get("nonexistent-id")
    assert thread is None

@pytest.mark.asyncio
async def test_list_recent(thread_store):
    """Test listing recent threads"""
    # Create and save multiple threads
    threads = []
    for i in range(3):
        thread = Thread(
            id=f"test-thread-{i}",
            title=f"Test Thread {i}"
        )
        thread.add_message(Message(role="user", content=f"Message {i}"))
        await thread_store.save(thread)
        threads.append(thread)
    
    # List recent threads
    recent_threads = await thread_store.list_recent(limit=2)
    assert len(recent_threads) == 2
    # Should be in reverse order (most recent first)
    assert recent_threads[0].id == "test-thread-2"
    assert recent_threads[1].id == "test-thread-1"

@pytest.mark.asyncio
async def test_delete_thread(thread_store, sample_thread):
    """Test deleting a thread"""
    # Save the thread first
    await thread_store.save(sample_thread)
    
    # Delete the thread
    success = await thread_store.delete(sample_thread.id)
    assert success is True
    
    # Verify it's gone
    async with thread_store.async_session() as session:
        async with session.begin():
            record = await session.get(ThreadRecord, sample_thread.id)
            assert record is None

@pytest.mark.asyncio
async def test_delete_nonexistent_thread(thread_store):
    """Test deleting a non-existent thread"""
    success = await thread_store.delete("nonexistent-id")
    assert success is False

@pytest.mark.asyncio
async def test_find_by_attributes(thread_store):
    """Test finding threads by attributes"""
    # Create threads with different attributes
    thread1 = Thread(id="thread-1", title="Thread 1")
    thread1.attributes = {"category": "work", "priority": "high"}
    await thread_store.save(thread1)
    
    thread2 = Thread(id="thread-2", title="Thread 2")
    thread2.attributes = {"category": "personal", "priority": "low"}
    await thread_store.save(thread2)
    
    # Search by attributes using SQLite JSON syntax
    async with thread_store.async_session() as session:
        async with session.begin():
            def find_threads():
                stmt = select(ThreadRecord).where(
                    text("json_extract(attributes, '$.category') = 'work'")
                )
                return session.execute(stmt)
            
            result = await greenlet_spawn(find_threads)
            records = result.scalars().all()
            
    assert len(records) == 1
    assert records[0].id == "thread-1"

@pytest.mark.asyncio
async def test_find_by_source(thread_store):
    """Test finding threads by source"""
    # Create threads with different sources
    thread1 = Thread(id="thread-1", title="Thread 1")
    thread1.source = {"name": "slack", "channel": "general"}
    await thread_store.save(thread1)
    
    thread2 = Thread(id="thread-2", title="Thread 2")
    thread2.source = {"name": "notion", "page_id": "123"}
    await thread_store.save(thread2)
    
    # Search by source using SQLite JSON syntax
    async with thread_store.async_session() as session:
        async with session.begin():
            def find_threads():
                stmt = select(ThreadRecord).where(
                    text("json_extract(source, '$.name') = 'slack'")
                )
                return session.execute(stmt)
            
            result = await greenlet_spawn(find_threads)
            records = result.scalars().all()
            
    assert len(records) == 1
    assert records[0].id == "thread-1"

@pytest.mark.asyncio
async def test_thread_update(thread_store, sample_thread):
    """Test updating an existing thread"""
    # Save the initial thread
    await thread_store.save(sample_thread)
    
    # Modify the thread
    sample_thread.title = "Updated Title"
    sample_thread.add_message(Message(role="assistant", content="Response"))
    
    # Save the updates
    await thread_store.save(sample_thread)
    
    # Verify the updates
    updated_thread = await thread_store.get(sample_thread.id)
    assert updated_thread.title == "Updated Title"
    assert len(updated_thread.messages) == 2
    assert updated_thread.messages[1].role == "assistant"
    assert updated_thread.messages[1].content == "Response"

@pytest.mark.asyncio
async def test_thread_store_default_url():
    """Test ThreadStore initialization with default URL."""
    store = ThreadStore()
    assert store.database_url.startswith("sqlite+aiosqlite:///")
    assert "tyler_threads" in store.database_url

@pytest.mark.asyncio
async def test_thread_store_temp_cleanup():
    """Test that temporary database files are cleaned up."""
    # Create store with temp directory
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = os.path.join(temp_dir, "threads.db")
        store = ThreadStore(f"sqlite+aiosqlite:///{db_path}")
        
        # Create tables
        async with store.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        # Save a thread
        thread = Thread(id="test-thread", title="Test Thread")
        await store.save(thread)
        
        # Verify thread was saved
        async with store.async_session() as session:
            async with session.begin():
                def get_thread():
                    return session.get(ThreadRecord, thread.id)
                
                record = await greenlet_spawn(get_thread)
                assert record is not None
                assert record.title == thread.title
        
        # Close store
        await store.engine.dispose()
        
        # Verify database file exists in temp directory
        assert os.path.exists(db_path)
    
    # After exiting temp directory context, verify it's gone
    assert not os.path.exists(db_path)

@pytest.mark.asyncio
async def test_thread_store_connection_management():
    """Test proper connection management."""
    store = ThreadStore(":memory:")
    
    # Create tables
    async with store.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create and save multiple threads
    threads = []
    for i in range(5):
        thread = Thread()
        await store.save(thread)
        threads.append(thread)
    
    # Verify all threads can be retrieved
    for thread in threads:
        retrieved = await store.get(thread.id)
        assert retrieved is not None
        assert retrieved.id == thread.id
    
    # Close all connections
    await store.engine.dispose()

@pytest.mark.asyncio
async def test_thread_store_concurrent_access():
    """Test concurrent access to thread store."""
    store = ThreadStore(":memory:")
    
    # Create tables
    async with store.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    thread = Thread()
    await store.save(thread)
    
    # Simulate concurrent access
    async def update_thread():
        # Each operation should get its own session
        retrieved = await store.get(thread.id)
        retrieved.title = "Updated"
        await store.save(retrieved)
    
    # Run multiple updates
    for _ in range(5):
        await update_thread()
    
    # Verify final state
    final = await store.get(thread.id)
    assert final.title == "Updated"
    
    await store.engine.dispose()

@pytest.mark.asyncio
async def test_thread_store_json_serialization():
    """Test JSON serialization of complex thread data."""
    store = ThreadStore(":memory:")
    
    # Create tables
    async with store.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    thread = Thread()
    
    # Add complex data
    thread.attributes = {
        "nested": {"key": "value"},
        "list": [1, 2, 3],
        "null": None,
        "bool": True
    }
    
    # Save and retrieve
    await store.save(thread)
    retrieved = await store.get(thread.id)
    
    # Verify complex data is preserved
    assert retrieved.attributes == thread.attributes
    
    await store.engine.dispose()

@pytest.mark.asyncio
async def test_thread_store_error_handling():
    """Test error handling in thread store operations."""
    store = ThreadStore(":memory:")
    
    # Create tables
    async with store.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Test invalid thread ID
    assert await store.get("nonexistent") is None
    
    # Test invalid JSON data
    thread = Thread()
    thread.attributes = {"invalid": object()}  # Object that can't be JSON serialized
    
    with pytest.raises(Exception):
        await store.save(thread)
        
    await store.engine.dispose()

@pytest.mark.asyncio
async def test_thread_store_pagination():
    """Test thread listing with pagination."""
    store = ThreadStore(":memory:")
    
    # Create tables
    async with store.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create 15 threads
    threads = []
    for i in range(15):
        thread = Thread()
        thread.title = f"Thread {i}"
        await store.save(thread)
        threads.append(thread)
    
    # Test different page sizes
    page1 = await store.list(limit=5)
    assert len(page1) == 5
    page2 = await store.list(limit=10, offset=5)
    assert len(page2) == 10
    all_threads = await store.list(limit=20)
    assert len(all_threads) == 15
    
    # Test ordering
    recent = await store.list(limit=5)
    assert recent[0].title == "Thread 14"  # Most recent first
    
    await store.engine.dispose() 