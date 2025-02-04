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
    Thread storage implementation using SQLAlchemy.
    Supports both PostgreSQL and SQLite backends.
    
    Key characteristics:
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
        store = ThreadStore("postgresql://user:pass@localhost/dbname")
        
        # SQLite for development
        store = ThreadStore("sqlite:///path/to/db.sqlite")
        
        # Must save threads and changes to persist
        thread = Thread()
        store.save_thread(thread)  # Required
        thread.add_message(message)
        store.save_thread(thread)  # Save changes
        
        # Always use thread.id with database storage
        result = await agent.go(thread.id)
        
    Note:
    Schema migrations (if needed) should be handled through SQLAlchemy's
    Alembic library. However, since we store thread data as JSON,
    most changes can be made without database migrations.
    """
    
    def __init__(self, database_url: Optional[str] = None):
        """
        Initialize thread store with database URL.
        
        Args:
            database_url: SQLAlchemy database URL. Examples:
                - "postgresql://user:pass@localhost/dbname"
                - "sqlite:///path/to/db.sqlite"
                - "sqlite:///:memory:"  # In-memory SQLite database
                
        If no URL is provided, uses a temporary SQLite database.
        """
        if database_url is None:
            # Create a temporary directory that persists until program exit
            tmp_dir = Path(tempfile.gettempdir()) / "tyler_threads"
            tmp_dir.mkdir(exist_ok=True)
            database_url = f"sqlite:///{tmp_dir}/threads.db"
            
        self.database_url = database_url
        self.engine = create_engine(self.database_url)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
    
    def save(self, thread: Thread) -> Thread:
        """Save a thread to the database."""
        session = self.Session()
        try:
            thread_data = thread.to_dict()
            record = session.query(ThreadRecord).get(thread.id)
            
            if record:
                record.data = thread_data
                record.updated_at = datetime.utcnow()
            else:
                record = ThreadRecord(
                    id=thread.id,
                    data=thread_data
                )
                session.add(record)
                
            session.commit()
            return thread
        finally:
            session.close()
    
    def get(self, thread_id: str) -> Optional[Thread]:
        """Get a thread by ID."""
        session = self.Session()
        try:
            record = session.query(ThreadRecord).get(thread_id)
            if record and record.data:
                return Thread(**record.data)
            return None
        finally:
            session.close()
    
    def delete_thread(self, thread_id: str) -> bool:
        """Delete a thread by ID."""
        session = self.Session()
        try:
            record = session.query(ThreadRecord).get(thread_id)
            if record:
                session.delete(record)
                session.commit()
                return True
            return False
        finally:
            session.close()
    
    def list_threads(self, limit: int = 100, offset: int = 0) -> List[Thread]:
        """List threads with pagination."""
        session = self.Session()
        try:
            records = session.query(ThreadRecord)\
                .order_by(ThreadRecord.updated_at.desc())\
                .limit(limit)\
                .offset(offset)\
                .all()
            return [Thread(**record.data) for record in records]
        finally:
            session.close()
            
    def find_by_attributes(self, attributes: Dict[str, Any]) -> List[Thread]:
        """Find threads by matching attributes."""
        session = self.Session()
        try:
            records = session.query(ThreadRecord).all()
            matching_threads = []
            
            for record in records:
                # Check if all requested attributes match
                if all(record.data.get("attributes", {}).get(k) == v for k, v in attributes.items()):
                    matching_threads.append(Thread(**record.data))
            
            return matching_threads
        finally:
            session.close()

    def find_by_source(self, source_name: str, properties: Dict[str, Any]) -> List[Thread]:
        """Find threads by source name and properties."""
        session = self.Session()
        try:
            records = session.query(ThreadRecord).all()
            matching_threads = []
            
            for record in records:
                source = record.data.get("source")
                if isinstance(source, dict) and source.get("name") == source_name:
                    # Check if all properties match
                    if all(source.get(k) == v for k, v in properties.items()):
                        matching_threads.append(Thread(**record.data))
            
            return matching_threads
        finally:
            session.close()
            
    def list_recent(self, limit: int = 30) -> List[Thread]:
        """List recent threads ordered by updated_at timestamp."""
        session = self.Session()
        try:
            records = session.query(ThreadRecord)\
                .order_by(ThreadRecord.updated_at.desc())\
                .limit(limit)\
                .all()
            return [Thread(**record.data) for record in records]
        finally:
            session.close()

# Alias the default store to SQLite
ThreadStore = ThreadStore

# Optional PostgreSQL/MySQL implementation
try:
    import psycopg2
    import mysqlclient
    
    class SQLAlchemyThreadStore(ThreadStore):
        """PostgreSQL/MySQL-based thread storage for production use."""
        
        def __init__(self, database_url: str):
            self.database_url = database_url
            self.engine = create_engine(self.database_url)
            Base.metadata.create_all(self.engine)
            self.Session = sessionmaker(bind=self.engine)
        
        # Implementation is identical to SQLiteThreadStore
        save = ThreadStore.save
        get = ThreadStore.get
        delete_thread = ThreadStore.delete_thread
        list_threads = ThreadStore.list_threads
        
except ImportError:
    pass 