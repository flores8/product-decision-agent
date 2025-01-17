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

class BaseThreadStore(ABC):
    """Abstract base class for thread storage."""
    
    @abstractmethod
    def save(self, thread) -> None:
        """Save a thread."""
        pass
    
    @abstractmethod
    def get(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a thread by ID."""
        pass
    
    @abstractmethod
    def delete(self, thread_id: str) -> bool:
        """Delete a thread by ID."""
        pass
    
    @abstractmethod
    def list_threads(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """List threads with pagination."""
        pass

class SQLiteThreadStore(BaseThreadStore):
    """SQLite-based thread storage. Default implementation."""
    
    def __init__(self, database_url: Optional[str] = None):
        """Initialize with optional database URL. If not provided, uses a temporary file."""
        if database_url is None:
            # Create a temporary directory that persists until program exit
            tmp_dir = Path(tempfile.gettempdir()) / "tyler_threads"
            tmp_dir.mkdir(exist_ok=True)
            database_url = f"sqlite:///{tmp_dir}/threads.db"
            
        self.database_url = database_url
        self.engine = create_engine(self.database_url)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
    
    def save(self, thread) -> None:
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
        finally:
            session.close()
    
    def get(self, thread_id: str) -> Optional[Thread]:
        session = self.Session()
        try:
            record = session.query(ThreadRecord).get(thread_id)
            if record and record.data:
                return Thread(**record.data)
            return None
        finally:
            session.close()
    
    def delete(self, thread_id: str) -> bool:
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
    
    def list_threads(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        session = self.Session()
        try:
            records = session.query(ThreadRecord)\
                .order_by(ThreadRecord.updated_at.desc())\
                .limit(limit)\
                .offset(offset)\
                .all()
            return [record.data for record in records]
        finally:
            session.close()
            
    def find_by_attributes(self, attributes: Dict[str, Any]) -> List[Thread]:
        """Find threads by matching attributes"""
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
        """Find threads by source name and properties"""
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
        """List recent threads ordered by updated_at timestamp.
        
        Args:
            limit: Maximum number of threads to return
            
        Returns:
            List of Thread objects ordered by most recently updated first
        """
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
ThreadStore = SQLiteThreadStore

# Optional PostgreSQL/MySQL implementation
try:
    import psycopg2
    import mysqlclient
    
    class SQLAlchemyThreadStore(BaseThreadStore):
        """PostgreSQL/MySQL-based thread storage for production use."""
        
        def __init__(self, database_url: str):
            self.database_url = database_url
            self.engine = create_engine(self.database_url)
            Base.metadata.create_all(self.engine)
            self.Session = sessionmaker(bind=self.engine)
        
        # Implementation is identical to SQLiteThreadStore
        save = SQLiteThreadStore.save
        get = SQLiteThreadStore.get
        delete = SQLiteThreadStore.delete
        list_threads = SQLiteThreadStore.list_threads
        
except ImportError:
    pass 