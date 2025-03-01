"""Thread storage implementation."""
from typing import Optional, Dict, Any, List, Union
from tyler.models.thread import Thread
from tyler.models.message import Message
from tyler.models.attachment import Attachment
from tyler.utils.logging import get_logger
from .storage_backend import StorageBackend, MemoryBackend, SQLBackend
from .models import Base
import os

logger = get_logger(__name__)

class ThreadStore:
    """
    Thread storage implementation with pluggable backends.
    Supports both in-memory and SQL (SQLite/PostgreSQL) storage.
    
    Key characteristics:
    - Unified interface for all storage types
    - Automatic backend selection based on configuration
    - Memory backend for development/testing
    - SQLite for local persistence
    - PostgreSQL for production
    
    Usage:
        # Memory storage (default)
        store = ThreadStore()
        
        # SQLite storage
        store = ThreadStore(database_url="sqlite+aiosqlite:///path/to/db.sqlite")
        
        # PostgreSQL storage
        store = ThreadStore(database_url="postgresql+asyncpg://user:pass@localhost/dbname")
        
        # Must initialize before using
        await store.initialize()
        
        # Thread operations
        thread = Thread()
        await store.save(thread)
        result = await store.get(thread.id)
    """
    
    def __init__(self, database_url: Optional[str] = None):
        """
        Initialize thread store with optional database URL.
        If no URL is provided and the environment variable 'TYLER_DB_TYPE' is set, use SQLBackend
        (configured via env vars), otherwise use in-memory storage.
        
        Args:
            database_url: SQLAlchemy async database URL. Examples:
                - "postgresql+asyncpg://user:pass@localhost/dbname"
                - "sqlite+aiosqlite:///path/to/db.sqlite"
                - ":memory:" or None for in-memory storage
        """
        if database_url is None:
            if os.environ.get("TYLER_DB_TYPE") is not None:
                # Use SQLBackend with default configuration
                self._backend = SQLBackend(None)
            else:
                self._backend = MemoryBackend()
        else:
            self._backend = SQLBackend(database_url)
    
    async def initialize(self) -> None:
        """Initialize the storage backend."""
        await self._backend.initialize()
    
    async def save(self, thread: Thread) -> Thread:
        """Save a thread to storage."""
        return await self._backend.save(thread)
    
    async def get(self, thread_id: str) -> Optional[Thread]:
        """Get a thread by ID."""
        return await self._backend.get(thread_id)
    
    async def delete(self, thread_id: str) -> bool:
        """Delete a thread by ID."""
        return await self._backend.delete(thread_id)
    
    async def list(self, limit: int = 100, offset: int = 0) -> List[Thread]:
        """List threads with pagination."""
        return await self._backend.list(limit, offset)
    
    async def find_by_attributes(self, attributes: Dict[str, Any]) -> List[Thread]:
        """Find threads by matching attributes."""
        return await self._backend.find_by_attributes(attributes)
    
    async def find_by_source(self, source_name: str, properties: Dict[str, Any]) -> List[Thread]:
        """Find threads by source name and properties."""
        return await self._backend.find_by_source(source_name, properties)
    
    async def list_recent(self, limit: Optional[int] = None) -> List[Thread]:
        """List recent threads."""
        return await self._backend.list_recent(limit)

    # Add properties to expose backend attributes
    @property
    def database_url(self):
        return getattr(self._backend, "database_url", None)

    @property
    def engine(self):
        return getattr(self._backend, "engine", None)

    @property
    def async_session(self):
        return getattr(self._backend, "async_session", None)

# For backward compatibility
MemoryThreadStore = ThreadStore  # Uses memory backend by default

# Optional PostgreSQL-specific implementation
try:
    import asyncpg
    
    class SQLAlchemyThreadStore(ThreadStore):
        """PostgreSQL-based thread storage for production use."""
        
        def __init__(self, database_url: str):
            if not database_url.startswith('postgresql+asyncpg://'):
                database_url = database_url.replace('postgresql://', 'postgresql+asyncpg://')
            super().__init__(database_url)
        
except ImportError:
    pass 