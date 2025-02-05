from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from datetime import datetime
import json
import os
from pathlib import Path
import tempfile
from sqlalchemy import create_engine, Column, String, JSON, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import select
from tyler.models.thread import Thread

Base = declarative_base()

class ThreadRecord(Base):
    __tablename__ = 'threads'
    
    id = Column(String, primary_key=True)
    data = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ThreadStore:
    """
    Thread storage implementation using async SQLAlchemy.
    Supports both PostgreSQL and SQLite backends.
    
    Key characteristics:
    - Async operations for non-blocking I/O
    - Persistent storage (data survives program restarts)
    - Cross-session support (can access threads from different processes)
    - Production-ready with PostgreSQL
    - Development-friendly with SQLite
    - Perfect for applications and services
    - Automatic schema management through SQLAlchemy
    
    Schema:
    The database schema is automatically created and managed by SQLAlchemy.
    No manual SQL scripts needed. The schema includes:
    - threads table:
        - id: String (primary key)
        - data: JSON (thread data)
        - created_at: DateTime
        - updated_at: DateTime
    
    Usage:
        # PostgreSQL for production
        store = ThreadStore("postgresql+asyncpg://user:pass@localhost/dbname")
        
        # SQLite for development
        store = ThreadStore("sqlite+aiosqlite:///path/to/db.sqlite")
        
        # Must save threads and changes to persist
        thread = Thread()
        await store.save(thread)  # Required
        thread.add_message(message)
        await store.save(thread)  # Save changes
        
        # Always use thread.id with database storage
        result = await agent.go(thread.id)
    """
    
    def __init__(self, database_url: Optional[str] = None):
        """
        Initialize thread store with database URL.
        
        Args:
            database_url: SQLAlchemy async database URL. Examples:
                - "postgresql+asyncpg://user:pass@localhost/dbname"
                - "sqlite+aiosqlite:///path/to/db.sqlite"
                - ":memory:" or "sqlite+aiosqlite:///:memory:"
                
        If no URL is provided, uses a temporary SQLite database.
        """
        if database_url is None:
            # Create a temporary directory that persists until program exit
            tmp_dir = Path(tempfile.gettempdir()) / "tyler_threads"
            tmp_dir.mkdir(exist_ok=True)
            database_url = f"sqlite+aiosqlite:///{tmp_dir}/threads.db"
        elif database_url == ":memory:":
            database_url = "sqlite+aiosqlite:///:memory:"
            
        self.database_url = database_url
        
        # Configure engine options
        engine_kwargs = {
            'echo': os.environ.get("TYLER_DB_ECHO", "").lower() == "true"
        }
        
        # Add pool configuration if specified and not using SQLite
        if not self.database_url.startswith('sqlite'):
            pool_size = os.environ.get("TYLER_DB_POOL_SIZE")
            max_overflow = os.environ.get("TYLER_DB_MAX_OVERFLOW")
            
            if pool_size is not None:
                engine_kwargs['pool_size'] = int(pool_size)
            if max_overflow is not None:
                engine_kwargs['max_overflow'] = int(max_overflow)
            
        self.engine = create_async_engine(self.database_url, **engine_kwargs)
        self.async_session = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )
    
    async def save(self, thread: Thread) -> Thread:
        """Save a thread to the database."""
        async with self.async_session() as session:
            async with session.begin():
                thread_data = thread.to_dict()
                record = await session.get(ThreadRecord, thread.id)
                
                if record:
                    record.data = thread_data
                    record.updated_at = datetime.utcnow()
                else:
                    record = ThreadRecord(
                        id=thread.id,
                        data=thread_data
                    )
                    session.add(record)
                
            return thread
    
    async def get(self, thread_id: str) -> Optional[Thread]:
        """Get a thread by ID."""
        async with self.async_session() as session:
            record = await session.get(ThreadRecord, thread_id)
            if record and record.data:
                return Thread(**record.data)
            return None
    
    async def delete(self, thread_id: str) -> bool:
        """Delete a thread by ID."""
        async with self.async_session() as session:
            async with session.begin():
                record = await session.get(ThreadRecord, thread_id)
                if record:
                    await session.delete(record)
                    return True
                return False
    
    async def list(self, limit: int = 100, offset: int = 0) -> List[Thread]:
        """List threads with pagination."""
        async with self.async_session() as session:
            result = await session.execute(
                select(ThreadRecord)
                .order_by(ThreadRecord.updated_at.desc())
                .limit(limit)
                .offset(offset)
            )
            records = result.scalars().all()
            return [Thread(**record.data) for record in records]
    
    async def find_by_attributes(self, attributes: Dict[str, Any]) -> List[Thread]:
        """Find threads by matching attributes."""
        async with self.async_session() as session:
            result = await session.execute(select(ThreadRecord))
            records = result.scalars().all()
            matching_threads = []
            
            for record in records:
                if all(record.data.get("attributes", {}).get(k) == v for k, v in attributes.items()):
                    matching_threads.append(Thread(**record.data))
            
            return matching_threads

    async def find_by_source(self, source_name: str, properties: Dict[str, Any]) -> List[Thread]:
        """Find threads by source name and properties."""
        async with self.async_session() as session:
            result = await session.execute(select(ThreadRecord))
            records = result.scalars().all()
            matching_threads = []
            
            for record in records:
                source = record.data.get("source")
                if isinstance(source, dict) and source.get("name") == source_name:
                    if all(source.get(k) == v for k, v in properties.items()):
                        matching_threads.append(Thread(**record.data))
            
            return matching_threads
            
    async def list_recent(self, limit: int = 30) -> List[Thread]:
        """List recent threads ordered by updated_at timestamp."""
        async with self.async_session() as session:
            result = await session.execute(
                select(ThreadRecord)
                .order_by(ThreadRecord.updated_at.desc())
                .limit(limit)
            )
            records = result.scalars().all()
            return [Thread(**record.data) for record in records]

# Base ThreadStore supports both SQLite and PostgreSQL through SQLAlchemy
ThreadStore = ThreadStore

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