from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from datetime import datetime, UTC
import json
import os
from pathlib import Path
import tempfile
from sqlalchemy import create_engine, Column, String, JSON, DateTime, Text, ForeignKey, select, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, selectinload
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from tyler.models.thread import Thread
from tyler.models.message import Message
from tyler.models.attachment import Attachment
from tyler.storage import get_file_store
from .models import Base, ThreadRecord, MessageRecord

Base = declarative_base()

class ThreadRecord(Base):
    __tablename__ = 'threads'
    
    id = Column(String, primary_key=True)
    title = Column(String, nullable=True)
    attributes = Column(JSON, nullable=False, default={})
    source = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    
    messages = relationship("MessageRecord", back_populates="thread", cascade="all, delete-orphan")

class MessageRecord(Base):
    __tablename__ = 'messages'
    
    id = Column(String, primary_key=True)
    thread_id = Column(String, ForeignKey('threads.id', ondelete='CASCADE'), nullable=False)
    sequence = Column(Integer, nullable=False)  # Message order in thread
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

    def _create_message_from_record(self, msg_record: MessageRecord) -> Message:
        """Helper method to create a Message from a MessageRecord"""
        message = Message(
            id=msg_record.id,
            role=msg_record.role,
            sequence=msg_record.sequence,
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
        return message

    def _create_thread_from_record(self, record: ThreadRecord) -> Thread:
        """Helper method to create a Thread from a ThreadRecord"""
        thread = Thread(
            id=record.id,
            title=record.title,
            attributes=record.attributes,
            source=record.source,
            created_at=record.created_at,
            updated_at=record.updated_at,
            messages=[]
        )
        # Sort messages: system messages first, then others by sequence
        sorted_messages = sorted(record.messages, 
            key=lambda m: (0 if m.role == "system" else 1, m.sequence))
        for msg_record in sorted_messages:
            message = self._create_message_from_record(msg_record)
            thread.messages.append(message)
        return thread

    def _create_message_record(self, message: Message, thread_id: str, sequence: int) -> MessageRecord:
        """Helper method to create a MessageRecord from a Message"""
        return MessageRecord(
            id=message.id,
            thread_id=thread_id,
            sequence=sequence,
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

    async def save(self, thread: Thread) -> Thread:
        """Save a thread and its messages to the database."""
        async with self.async_session() as session:
            # Get existing thread if it exists
            stmt = select(ThreadRecord).options(selectinload(ThreadRecord.messages)).where(ThreadRecord.id == thread.id)
            result = await session.execute(stmt)
            thread_record = result.scalar_one_or_none()
            
            if thread_record:
                # Update existing thread
                thread_record.title = thread.title
                thread_record.attributes = thread.attributes
                thread_record.source = thread.source
                thread_record.updated_at = datetime.now(UTC)
                thread_record.messages = []  # Clear existing messages
            else:
                # Create new thread record
                thread_record = ThreadRecord(
                    id=thread.id,
                    title=thread.title,
                    attributes=thread.attributes,
                    source=thread.source,
                    created_at=thread.created_at,
                    updated_at=thread.updated_at,
                    messages=[]
                )
            
            # Process messages in order
            sequence = 1
            
            # First handle system messages
            for message in thread.messages:
                if message.role == "system":
                    if message.attachments:
                        await message.ensure_attachments_stored()
                    thread_record.messages.append(self._create_message_record(message, thread.id, sequence))
                    sequence += 1
            
            # Then handle non-system messages
            for message in thread.messages:
                if message.role != "system":
                    if message.attachments:
                        await message.ensure_attachments_stored()
                    thread_record.messages.append(self._create_message_record(message, thread.id, sequence))
                    sequence += 1
            
            session.add(thread_record)
            await session.commit()
            return thread

    async def get(self, thread_id: str) -> Optional[Thread]:
        """Get a thread by ID."""
        async with self.async_session() as session:
            stmt = select(ThreadRecord).options(selectinload(ThreadRecord.messages)).where(ThreadRecord.id == thread_id)
            result = await session.execute(stmt)
            thread_record = result.scalar_one_or_none()
            return self._create_thread_from_record(thread_record) if thread_record else None
    
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
            return [self._create_thread_from_record(record) for record in result.scalars().all()]
    
    async def find_by_attributes(self, attributes: Dict[str, Any]) -> List[Thread]:
        """Find threads by matching attributes."""
        async with self.async_session() as session:
            query = select(ThreadRecord).options(selectinload(ThreadRecord.messages))
            for key, value in attributes.items():
                query = query.where(ThreadRecord.attributes[key].astext == str(value))
            result = await session.execute(query)
            return [self._create_thread_from_record(record) for record in result.scalars().all()]

    async def find_by_source(self, source_name: str, properties: Dict[str, Any]) -> List[Thread]:
        """Find threads by source name and properties."""
        async with self.async_session() as session:
            query = select(ThreadRecord).options(selectinload(ThreadRecord.messages)).where(ThreadRecord.source['name'].astext == source_name)
            for key, value in properties.items():
                query = query.where(ThreadRecord.source[key].astext == str(value))
            result = await session.execute(query)
            return [self._create_thread_from_record(record) for record in result.scalars().all()]
            
    async def list_recent(self, limit: int = 30) -> List[Thread]:
        """List recent threads ordered by updated_at timestamp."""
        async with self.async_session() as session:
            result = await session.execute(
                select(ThreadRecord)
                .options(selectinload(ThreadRecord.messages))
                .order_by(ThreadRecord.updated_at.desc())
                .limit(limit)
            )
            return [self._create_thread_from_record(record) for record in result.scalars().all()]

    async def delete(self, thread_id: str) -> bool:
        """Delete a thread by ID."""
        async with self.async_session() as session:
            async with session.begin():
                record = await session.get(ThreadRecord, thread_id)
                if record:
                    await session.delete(record)
                    return True
                return False

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