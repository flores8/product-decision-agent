from sqlalchemy import create_engine, Column, String, JSON, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime
from typing import List, Optional
from pathlib import Path
from models.thread import Thread
import json

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

class ThreadStore:
    def __init__(self, db_name: str = "threads.db"):
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
            
            record = ThreadRecord(
                id=thread.id,
                title=thread.title,
                messages=messages_json,
                created_at=thread.created_at,
                updated_at=thread.updated_at,
                attributes=attributes_json
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
                return Thread(
                    id=record.id,
                    title=record.title,
                    messages=record.messages,
                    created_at=record.created_at,
                    updated_at=record.updated_at,
                    attributes=record.attributes
                )
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
            return [
                Thread(
                    id=record.id,
                    title=record.title,
                    messages=record.messages,
                    created_at=record.created_at,
                    updated_at=record.updated_at,
                    attributes=record.attributes
                ) for record in records
            ]
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