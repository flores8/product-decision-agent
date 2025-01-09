from sqlalchemy import create_engine, Column, String, JSON, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path
from models.thread import Thread
import json
import logging

logger = logging.getLogger(__name__)

Base = declarative_base()

class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

class ThreadRecord(Base):
    __tablename__ = 'threads'
    
    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    messages = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    attributes = Column(JSON, default=dict)
    source = Column(JSON, nullable=True)

class ThreadStore:
    def __init__(self, db_name: str = "threads.db"):
        if db_name == ":memory:":
            # For in-memory database, use special SQLite URL
            self.engine = create_engine("sqlite:///:memory:")
        else:
            # Create database directory if it doesn't exist
            db_dir = Path("database")
            db_dir.mkdir(exist_ok=True)
            
            db_path = db_dir / db_name
            self.engine = create_engine(f"sqlite:///{db_path}")
            
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def save(self, thread: Thread) -> str:
        """Save or update a thread"""
        session = self.Session()
        try:
            # Convert messages to JSON-serializable format with datetime handling
            messages_json = json.loads(
                json.dumps([msg.model_dump() for msg in thread.messages], 
                cls=DateTimeEncoder)
            )
            
            # Convert attributes to JSON-serializable format
            attributes_json = json.loads(
                json.dumps(thread.attributes, 
                cls=DateTimeEncoder)
            )
            
            # Convert source to JSON-serializable format if it exists
            source_json = None
            if thread.source:
                source_json = json.loads(
                    json.dumps(thread.source,
                    cls=DateTimeEncoder)
                )
            
            record = ThreadRecord(
                id=thread.id,
                title=thread.title,
                messages=messages_json,
                created_at=thread.created_at,
                updated_at=thread.updated_at,
                attributes=attributes_json,
                source=source_json
            )
            session.merge(record)  # merge will update if exists, insert if not
            session.commit()
            return thread.id
        finally:
            session.close()

    def get(self, thread_id: str) -> Optional[Thread]:
        """Retrieve a thread by ID"""
        if not thread_id:
            return None
            
        session = self.Session()
        try:
            record = session.query(ThreadRecord).get(thread_id)
            if record:
                return self._record_to_thread(record)
            return None
        finally:
            session.close()

    def list_recent(self, limit: int = 10) -> List[Thread]:
        """Get recent threads"""
        session = self.Session()
        try:
            records = session.query(ThreadRecord)\
                .order_by(ThreadRecord.updated_at.desc())\
                .limit(limit)\
                .all()
            return [self._record_to_thread(record) for record in records]
        finally:
            session.close()

    def delete(self, thread_id: str) -> bool:
        """Delete a thread"""
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

    def find_by_attributes(self, attributes: Dict[str, Any]) -> List[Thread]:
        """Find threads by matching attributes"""
        session = self.Session()
        try:
            records = session.query(ThreadRecord).all()
            matching_threads = []
            
            for record in records:
                # Check if all requested attributes match
                if all(record.attributes.get(k) == v for k, v in attributes.items()):
                    matching_threads.append(self._record_to_thread(record))
            
            return matching_threads
        finally:
            session.close()

    def find_by_source(self, source_name: str, properties: Dict[str, Any]) -> List[Thread]:
        """Find threads by source name and properties"""
        session = self.Session()
        try:
            logger.info(f"Looking up threads with source_name: {source_name} and properties: {properties}")
            records = session.query(ThreadRecord).all()
            logger.info(f"Found {len(records)} total threads")
            
            matching_threads = []
            for record in records:
                source = record.source
                logger.info(f"Thread {record.id} source: {source}")
                
                if isinstance(source, dict) and source.get("name") == source_name:
                    # Check if all properties match
                    if all(source.get(k) == v for k, v in properties.items()):
                        logger.info(f"Found matching thread: {record.id}")
                        matching_threads.append(self._record_to_thread(record))
                    else:
                        logger.info(f"Thread {record.id} properties didn't match. Source: {source}, Required: {properties}")
                else:
                    logger.info(f"Thread {record.id} source name didn't match. Source: {source}, Required: {source_name}")
            
            logger.info(f"Returning {len(matching_threads)} matching threads")
            return matching_threads
        finally:
            session.close()
            
    def _record_to_thread(self, record: ThreadRecord) -> Thread:
        """Convert a database record to a Thread object"""
        return Thread(
            id=record.id,
            title=record.title,
            messages=record.messages,
            created_at=record.created_at,
            updated_at=record.updated_at,
            attributes=record.attributes,
            source=record.source
        ) 