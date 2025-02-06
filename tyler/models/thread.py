from typing import List, Dict, Optional, Literal, Any
from datetime import datetime, UTC
from pydantic import BaseModel, Field, field_validator
from tyler.models.message import Message
from litellm import completion
import uuid
import weave

class Thread(BaseModel):
    """Represents a thread containing multiple messages"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: Optional[str] = Field(default="Untitled Thread")
    messages: List[Message] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
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
    
    @field_validator("created_at", "updated_at", mode="before")
    def ensure_timezone(cls, value: datetime) -> datetime:
        """Ensure all datetime fields are timezone-aware UTC"""
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value

    def to_dict(self) -> Dict[str, Any]:
        """Convert thread to a dictionary suitable for JSON serialization"""
        return {
            "id": self.id,
            "title": self.title,
            "messages": [msg.model_dump() for msg in self.messages],
            "created_at": self.created_at.isoformat(),  # Will automatically include timezone
            "updated_at": self.updated_at.isoformat(),  # Will automatically include timezone
            "attributes": self.attributes,
            "source": self.source
        }
    
    def ensure_system_prompt(self, prompt: str) -> None:
        """Ensures system prompt is first message, adding or updating if needed"""
        if not self.messages or self.messages[0].role != "system":
            self.messages.insert(0, Message(role="system", content=prompt))
            self.updated_at = datetime.now(UTC)
        elif self.messages[0].content != prompt:
            self.messages[0].content = prompt
            self.updated_at = datetime.now(UTC)

    def add_message(self, message: Message) -> None:
        """Add a new message to the thread"""
        self.messages.append(message)
        self.updated_at = datetime.now(UTC)
        
        # Update title if not set and this is the first user message
        if self.title == "Untitled Thread" and message.role == "user":
            # Get first 30 chars of message content, handling both string and list content types
            content = message.content
            if isinstance(content, list):
                # For multimodal messages, find the first text content
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "text":
                        content = item.get("text", "")
                        break
                else:
                    content = ""
            
            if content:
                # Only add ellipsis if we actually truncated the content
                if len(content) > 30:
                    self.title = content[:30] + "..."
                else:
                    self.title = content

    def get_messages_for_chat_completion(self) -> List[Dict]:
        """Return messages in the format expected by chat completion APIs"""
        return [msg.to_chat_completion_message() for msg in self.messages]

    def clear_messages(self) -> None:
        """Clear all messages from the thread"""
        self.messages = []
        self.updated_at = datetime.now(UTC)

    def get_last_message_by_role(self, role: Literal["user", "assistant", "system", "tool"]) -> Optional[Message]:
        """Return the last message with the specified role, or None if no messages exist with that role"""
        messages = [m for m in self.messages if m.role == role]
        return messages[-1] if messages else None
        
    @weave.op()
    def generate_title(self) -> str:
        """Generate a concise title for the thread using GPT-4o"""
        if not self.messages:
            return "Empty Thread"
        
        # Prepare messages for the title generation
        system_prompt = "You are a title generator. Generate a clear, concise title (less than 10 words) that captures the main topic or purpose of this conversation. Return only the title, nothing else."
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Generate a title for this conversation:\n\n{[msg.model_dump() for msg in self.messages]}"}
        ]
        
        response = completion(
            model="gpt-4o",
            messages=messages,
            temperature=0.7,
            max_tokens=50
        )
        
        new_title = response.choices[0].message.content.strip()
        self.title = new_title
        self.updated_at = datetime.now(UTC)
        return new_title