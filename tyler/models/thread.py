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
    
    # Simple metrics structure
    metrics: Dict[str, Any] = Field(
        default_factory=lambda: {
            "completion_tokens": 0,
            "prompt_tokens": 0,
            "total_tokens": 0,
            "model_usage": {}  # {"gpt-4": {"calls": 0, "completion_tokens": 0, "prompt_tokens": 0, "total_tokens": 0}}
        }
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": "thread-123",
                    "title": "Example Thread",
                    "messages": [],
                    "created_at": "2024-02-07T00:00:00+00:00",
                    "updated_at": "2024-02-07T00:00:00+00:00",
                    "attributes": {},
                    "source": {
                        "name": "slack",
                        "channel": "C123",
                        "thread_ts": "1234567890.123"
                    },
                    "metrics": {
                        "completion_tokens": 0,
                        "prompt_tokens": 0,
                        "total_tokens": 0,
                        "model_usage": {
                            "gpt-4o": {
                                "calls": 0,
                                "completion_tokens": 0,
                                "prompt_tokens": 0,
                                "total_tokens": 0
                            }
                        }
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
            "source": self.source,
            "metrics": self.metrics
        }
    
    def ensure_system_prompt(self, prompt: str) -> None:
        """Ensures a system prompt exists as the first message in the thread.
        
        If no system message exists at the start of the thread, adds one.
        Does not modify any existing system messages.
        """
        if not self.messages or self.messages[0].role != "system":
            self.messages.insert(0, Message(role="system", content=prompt))
            self.updated_at = datetime.now(UTC)

    def add_message(self, message: Message) -> None:
        """Add a new message to the thread and update analytics"""
        self.messages.append(message)
        self.updated_at = datetime.now(UTC)
        
        # Update usage stats if applicable
        if message.metrics:
            # Update total token counts
            if message.metrics.get("completion_tokens"):
                self.metrics["completion_tokens"] += message.metrics["completion_tokens"]
            if message.metrics.get("prompt_tokens"):
                self.metrics["prompt_tokens"] += message.metrics["prompt_tokens"]
            if message.metrics.get("total_tokens"):
                self.metrics["total_tokens"] += message.metrics["total_tokens"]
            
            # Update per-model usage stats
            if message.metrics.get("model"):
                model = message.metrics["model"]
                if model not in self.metrics["model_usage"]:
                    self.metrics["model_usage"][model] = {
                        "calls": 0,
                        "completion_tokens": 0,
                        "prompt_tokens": 0,
                        "total_tokens": 0
                    }
                self.metrics["model_usage"][model]["calls"] += 1
                
                if message.metrics.get("completion_tokens"):
                    self.metrics["model_usage"][model]["completion_tokens"] += message.metrics["completion_tokens"]
                if message.metrics.get("prompt_tokens"):
                    self.metrics["model_usage"][model]["prompt_tokens"] += message.metrics["prompt_tokens"]
                if message.metrics.get("total_tokens"):
                    self.metrics["model_usage"][model]["total_tokens"] += message.metrics["total_tokens"]
        
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
        
        # Get thread messages excluding system prompt and combine them into a single conversation string
        thread_messages = [msg.to_chat_completion_message() for msg in self.messages if msg.role != "system"]
        conversation = "\n".join([f"{msg['role']}: {msg['content']}" for msg in thread_messages])
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Generate a title for this conversation:\n\n{conversation}"}
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