from sqlalchemy import create_engine, Column, String, JSON, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime
from typing import List, Optional
from pathlib import Path
from models.conversation import Conversation
import json

Base = declarative_base()

class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

class ConversationRecord(Base):
    __tablename__ = 'conversations'
    
    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    messages = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    attributes = Column(JSON, default=dict)

class ConversationStore:
    def __init__(self, db_name: str = "conversations.db"):
        # Create database directory if it doesn't exist
        db_dir = Path("database")
        db_dir.mkdir(exist_ok=True)
        
        db_path = db_dir / db_name
        self.engine = create_engine(f"sqlite:///{db_path}")
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def save(self, conversation: Conversation) -> str:
        """Save or update a conversation"""
        session = self.Session()
        try:
            # Convert messages to JSON-serializable format with datetime handling
            messages_json = json.loads(
                json.dumps([msg.model_dump() for msg in conversation.messages], 
                cls=DateTimeEncoder)
            )
            
            # Convert attributes to JSON-serializable format
            attributes_json = json.loads(
                json.dumps(conversation.attributes, 
                cls=DateTimeEncoder)
            )
            
            record = ConversationRecord(
                id=conversation.id,
                title=conversation.title,
                messages=messages_json,
                created_at=conversation.created_at,
                updated_at=conversation.updated_at,
                attributes=attributes_json
            )
            session.merge(record)  # merge will update if exists, insert if not
            session.commit()
            return conversation.id
        finally:
            session.close()

    def get(self, conversation_id: str) -> Optional[Conversation]:
        """Retrieve a conversation by ID"""
        session = self.Session()
        try:
            record = session.query(ConversationRecord).get(conversation_id)
            if record:
                return Conversation(
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

    def list_recent(self, limit: int = 10) -> List[Conversation]:
        """Get recent conversations"""
        session = self.Session()
        try:
            records = session.query(ConversationRecord)\
                .order_by(ConversationRecord.updated_at.desc())\
                .limit(limit)\
                .all()
            return [
                Conversation(
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

    def delete(self, conversation_id: str) -> bool:
        """Delete a conversation"""
        session = self.Session()
        try:
            record = session.query(ConversationRecord).get(conversation_id)
            if record:
                session.delete(record)
                session.commit()
                return True
            return False
        finally:
            session.close() 