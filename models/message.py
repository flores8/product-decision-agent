from typing import Dict, Optional, Literal, Any
from datetime import datetime
from pydantic import BaseModel, Field
import hashlib
import json
import logging

logger = logging.getLogger(__name__)

class Message(BaseModel):
    """Represents a single message in a thread"""
    id: str = None  # Will be set in __init__
    role: Literal["system", "user", "assistant", "function"]
    content: str
    name: Optional[str] = None
    attributes: Dict = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    source: Optional[Dict[str, Any]] = None  # {"name": "slack", "thread_id": "..."}

    def __init__(self, **data):
        super().__init__(**data)
        if not self.id:
            # Create a hash of relevant properties
            hash_content = {
                "role": self.role,
                "content": self.content
            }
            # Only include name for function messages
            if self.role == "function" and self.name:
                hash_content["name"] = self.name
                
            if self.source:
                hash_content["source"] = self.source
            
            # Create deterministic JSON string for hashing
            hash_str = json.dumps(hash_content, sort_keys=True)
            self.id = hashlib.sha256(hash_str.encode()).hexdigest()
            logger.debug(f"Generated message ID {self.id} from hash content: {hash_str}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert message to a dictionary suitable for JSON serialization"""
        return {
            "id": self.id,
            "role": self.role,
            "content": self.content,
            "name": self.name,
            "attributes": self.attributes,
            "timestamp": self.timestamp.isoformat(),
            "source": self.source
        }
        
    def to_chat_completion_message(self) -> Dict[str, str]:
        """Return message in the format expected by chat completion APIs"""
        message_dict = {
            "role": self.role,
            "content": self.content
        }
        
        # Only include name if it exists and role is 'function'
        if self.name and self.role == "function":
            message_dict["name"] = self.name
            
        return message_dict

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "role": "user",
                    "content": "Hello, how are you?",
                    "name": None,
                    "attributes": {},
                    "source": {
                        "name": "slack",
                        "thread_id": "1234567890.123456"
                    }
                }
            ]
        }
    } 