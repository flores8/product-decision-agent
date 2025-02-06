from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from datetime import datetime, UTC
import json
import os
from pathlib import Path
import tempfile
from sqlalchemy import create_engine, Column, String, JSON, DateTime, Text, ForeignKey, select
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, selectinload
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from tyler.models.thread import Thread
from tyler.models.message import Message, Attachment

Base = declarative_base()

class ThreadRecord(Base):
    __tablename__ = 'threads'
    
    id = Column(String, primary_key=True)
    title = Column(String, nullable=True)
    attributes = Column(JSON, nullable=False, default={})
    source = Column(JSON, nullable=True)
    metrics = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    
    messages = relationship("MessageRecord", back_populates="thread", cascade="all, delete-orphan")

class MessageRecord(Base):
    __tablename__ = 'messages'
    
    id = Column(String, primary_key=True)
    thread_id = Column(String, ForeignKey('threads.id', ondelete='CASCADE'), nullable=False)
    role = Column(String, nullable=False)
    content = Column(Text, nullable=True)
    name = Column(String, nullable=True)
    tool_call_id = Column(String, nullable=True)
    tool_calls = Column(JSON, nullable=True)
    attributes = Column(JSON, nullable=False, default={})
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    source = Column(JSON, nullable=True)
    attachments = Column(JSON, nullable=True)
    metrics = Column(JSON, nullable=False)
    
    thread = relationship("ThreadRecord", back_populates="messages")

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
        await store.initialize()  # Must call this before using
        
        # SQLite for development
        store = ThreadStore("sqlite+aiosqlite:///path/to/db.sqlite")
        await store.initialize()  # Must call this before using
        
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

    async def initialize(self):
        """Initialize the database by creating tables if they don't exist."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def save(self, thread: Thread) -> Thread:
        """Save a thread and its messages to the database."""
        async with self.async_session() as session:
            async with session.begin():
                # Get or create thread record
                stmt = select(ThreadRecord).options(selectinload(ThreadRecord.messages)).where(ThreadRecord.id == thread.id)
                result = await session.execute(stmt)
                thread_record = result.scalar_one_or_none()
                
                if not thread_record:
                    thread_record = ThreadRecord(
                        id=thread.id,
                        title=thread.title,
                        attributes=thread.attributes,
                        source=thread.source,
                        metrics=thread.metrics
                    )
                    session.add(thread_record)
                else:
                    thread_record.title = thread.title
                    thread_record.attributes = thread.attributes
                    thread_record.source = thread.source
                    thread_record.metrics = thread.metrics
                    thread_record.updated_at = datetime.now(UTC)
                
                # Update messages
                existing_messages = {m.id: m for m in thread_record.messages}
                for message in thread.messages:
                    if message.id in existing_messages:
                        # Message exists, update if needed
                        msg_record = existing_messages[message.id]
                        msg_record.content = message.content
                        msg_record.metrics = message.metrics
                        msg_record.attachments = [a.model_dump() for a in message.attachments] if message.attachments else None
                    else:
                        # Create new message
                        msg_record = MessageRecord(
                            id=message.id,
                            thread_id=thread.id,
                            role=message.role,
                            content=message.content,
                            name=message.name,
                            tool_call_id=message.tool_call_id,
                            tool_calls=message.tool_calls,
                            attributes=message.attributes,
                            timestamp=message.timestamp,
                            source=message.source,
                            attachments=[a.model_dump() for a in message.attachments] if message.attachments else None,
                            metrics=message.metrics
                        )
                        session.add(msg_record)
                
            return thread

    async def get(self, thread_id: str) -> Optional[Thread]:
        """Get a thread by ID."""
        async with self.async_session() as session:
            # Get thread with all its messages
            stmt = select(ThreadRecord).options(selectinload(ThreadRecord.messages)).where(ThreadRecord.id == thread_id)
            result = await session.execute(stmt)
            thread_record = result.scalar_one_or_none()
            
            if not thread_record:
                return None
            
            # Convert to Thread model
            messages = []
            for msg_record in thread_record.messages:
                message = Message(
                    id=msg_record.id,
                    role=msg_record.role,
                    content=msg_record.content,
                    name=msg_record.name,
                    tool_call_id=msg_record.tool_call_id,
                    tool_calls=msg_record.tool_calls,
                    attributes=msg_record.attributes,
                    timestamp=msg_record.timestamp,
                    source=msg_record.source,
                    metrics=msg_record.metrics
                )
                if msg_record.attachments:
                    message.attachments = [Attachment(**a) for a in msg_record.attachments]
                messages.append(message)
            
            return Thread(
                id=thread_record.id,
                title=thread_record.title,
                messages=messages,
                attributes=thread_record.attributes,
                source=thread_record.source,
                metrics=thread_record.metrics,
                created_at=thread_record.created_at,
                updated_at=thread_record.updated_at
            )
    
    def _deserialize_thread_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Helper method to deserialize thread data from JSON."""
        data = data.copy()
        if 'created_at' in data:
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if 'updated_at' in data:
            data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        if 'messages' in data:
            for message in data['messages']:
                if 'created_at' in message:
                    message['created_at'] = datetime.fromisoformat(message['created_at'])
                if 'timestamp' in message:
                    message['timestamp'] = datetime.fromisoformat(message['timestamp'])
        return data

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
                .options(selectinload(ThreadRecord.messages))
                .order_by(ThreadRecord.updated_at.desc())
                .limit(limit)
                .offset(offset)
            )
            records = result.scalars().all()
            
            threads = []
            for record in records:
                thread = Thread(
                    id=record.id,
                    title=record.title,
                    attributes=record.attributes,
                    source=record.source,
                    metrics=record.metrics,
                    created_at=record.created_at,
                    updated_at=record.updated_at,
                    messages=[]
                )
                # Load messages for each thread
                for msg_record in record.messages:
                    message = Message(
                        id=msg_record.id,
                        role=msg_record.role,
                        content=msg_record.content,
                        name=msg_record.name,
                        tool_call_id=msg_record.tool_call_id,
                        tool_calls=msg_record.tool_calls,
                        attributes=msg_record.attributes,
                        timestamp=msg_record.timestamp,
                        source=msg_record.source,
                        metrics=msg_record.metrics
                    )
                    if msg_record.attachments:
                        message.attachments = [Attachment(**a) for a in msg_record.attachments]
                    thread.messages.append(message)
                threads.append(thread)
            return threads
    
    async def find_by_attributes(self, attributes: Dict[str, Any]) -> List[Thread]:
        """Find threads by matching attributes."""
        async with self.async_session() as session:
            # Build query to match all attributes
            query = select(ThreadRecord).options(selectinload(ThreadRecord.messages))
            for key, value in attributes.items():
                query = query.where(ThreadRecord.attributes[key].astext == str(value))
            
            result = await session.execute(query)
            records = result.scalars().all()
            
            threads = []
            for record in records:
                thread = Thread(
                    id=record.id,
                    title=record.title,
                    attributes=record.attributes,
                    source=record.source,
                    metrics=record.metrics,
                    created_at=record.created_at,
                    updated_at=record.updated_at,
                    messages=[]
                )
                for msg_record in record.messages:
                    message = Message(
                        id=msg_record.id,
                        role=msg_record.role,
                        content=msg_record.content,
                        name=msg_record.name,
                        tool_call_id=msg_record.tool_call_id,
                        tool_calls=msg_record.tool_calls,
                        attributes=msg_record.attributes,
                        timestamp=msg_record.timestamp,
                        source=msg_record.source,
                        metrics=msg_record.metrics
                    )
                    if msg_record.attachments:
                        message.attachments = [Attachment(**a) for a in msg_record.attachments]
                    thread.messages.append(message)
                threads.append(thread)
            return threads

    async def find_by_source(self, source_name: str, properties: Dict[str, Any]) -> List[Thread]:
        """Find threads by source name and properties."""
        async with self.async_session() as session:
            # Build query to match source properties
            query = select(ThreadRecord).options(selectinload(ThreadRecord.messages)).where(ThreadRecord.source['name'].astext == source_name)
            for key, value in properties.items():
                query = query.where(ThreadRecord.source[key].astext == str(value))
            
            result = await session.execute(query)
            records = result.scalars().all()
            
            threads = []
            for record in records:
                thread = Thread(
                    id=record.id,
                    title=record.title,
                    attributes=record.attributes,
                    source=record.source,
                    metrics=record.metrics,
                    created_at=record.created_at,
                    updated_at=record.updated_at,
                    messages=[]
                )
                for msg_record in record.messages:
                    message = Message(
                        id=msg_record.id,
                        role=msg_record.role,
                        content=msg_record.content,
                        name=msg_record.name,
                        tool_call_id=msg_record.tool_call_id,
                        tool_calls=msg_record.tool_calls,
                        attributes=msg_record.attributes,
                        timestamp=msg_record.timestamp,
                        source=msg_record.source,
                        metrics=msg_record.metrics
                    )
                    if msg_record.attachments:
                        message.attachments = [Attachment(**a) for a in msg_record.attachments]
                    thread.messages.append(message)
                threads.append(thread)
            return threads
            
    async def list_recent(self, limit: int = 30) -> List[Thread]:
        """List recent threads ordered by updated_at timestamp."""
        async with self.async_session() as session:
            result = await session.execute(
                select(ThreadRecord)
                .options(selectinload(ThreadRecord.messages))
                .order_by(ThreadRecord.updated_at.desc())
                .limit(limit)
            )
            records = result.scalars().all()
            
            threads = []
            for record in records:
                thread = Thread(
                    id=record.id,
                    title=record.title,
                    attributes=record.attributes,
                    source=record.source,
                    metrics=record.metrics,
                    created_at=record.created_at,
                    updated_at=record.updated_at,
                    messages=[]
                )
                for msg_record in record.messages:
                    message = Message(
                        id=msg_record.id,
                        role=msg_record.role,
                        content=msg_record.content,
                        name=msg_record.name,
                        tool_call_id=msg_record.tool_call_id,
                        tool_calls=msg_record.tool_calls,
                        attributes=msg_record.attributes,
                        timestamp=msg_record.timestamp,
                        source=msg_record.source,
                        metrics=msg_record.metrics
                    )
                    if msg_record.attachments:
                        message.attachments = [Attachment(**a) for a in msg_record.attachments]
                    thread.messages.append(message)
                threads.append(thread)
            return threads

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