from typing import List, Dict, Optional, Literal, Any
from datetime import datetime
from pydantic import BaseModel, Field
from tyler.models.message import Message
import uuid

class Thread(BaseModel):
    """Represents a thread containing multiple messages"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: Optional[str] = Field(default="Untitled Thread")
    messages: List[Message] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    attributes: Dict = Field(default_factory=dict)
    source: Optional[Dict[str, Any]] = None  # {"name": "slack", "thread_id": "..."}

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": "thread-123",
                    "title": "Example Thread",
                    "messages": [],
                    "attributes": {},
                    "source": {
                        "name": "slack",
                        "channel": "C123",
                        "thread_ts": "1234567890.123"
                    }
                }
            ]
        }
    }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert thread to a dictionary suitable for JSON serialization"""
        return {
            "id": self.id,
            "title": self.title,
            "messages": [msg.model_dump() for msg in self.messages],
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "attributes": self.attributes,
            "source": self.source
        }
    
    def ensure_system_prompt(self, prompt: str) -> None:
        """Ensures system prompt is first message, adding or updating if needed"""
        if not self.messages or self.messages[0].role != "system":
            self.messages.insert(0, Message(role="system", content=prompt))
        elif self.messages[0].content != prompt:
            self.messages[0].content = prompt

    def add_message(self, message: Message) -> None:
        """Add a new message to the thread"""
        self.messages.append(message)
        self.updated_at = datetime.utcnow()

    def get_messages_for_chat_completion(self) -> List[Dict]:
        """Return messages in the format expected by chat completion APIs"""
        return [msg.to_chat_completion_message() for msg in self.messages]

    def clear_messages(self) -> None:
        """Clear all messages from the thread"""
        self.messages = []
        self.updated_at = datetime.utcnow()

    def get_last_message_by_role(self, role: Literal["user", "assistant", "system", "tool"]) -> Optional[Message]:
        """Return the last message with the specified role, or None if no messages exist with that role"""
        messages = [m for m in self.messages if m.role == role]
        return messages[-1] if messages else None