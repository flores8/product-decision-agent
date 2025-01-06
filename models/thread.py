from typing import List, Dict, Optional, Literal, Any
from datetime import datetime
from pydantic import BaseModel, Field
from .message import Message
import uuid

class Thread(BaseModel):
    """Represents a thread containing multiple messages"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
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
        api_messages = []
        for msg in self.messages:
            message_dict = {
                "role": msg.role,
                "content": msg.content
            }
            
            # Only include name if it exists and role is 'function'
            if msg.name and msg.role == "function":
                message_dict["name"] = msg.name
                
            api_messages.append(message_dict)
        
        return api_messages

    def clear_messages(self) -> None:
        """Clear all messages from the thread"""
        self.messages = []
        self.updated_at = datetime.utcnow()

    def get_last_message_by_role(self, role: Literal["user", "assistant", "system", "function"]) -> Optional[Message]:
        """Return the last message with the specified role, or None if no messages exist with that role"""
        messages = [m for m in self.messages if m.role == role]
        return messages[-1] if messages else None