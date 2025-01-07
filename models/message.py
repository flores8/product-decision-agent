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

    def __init__(self, **data):
        super().__init__(**data)
        if not self.id:
            # Create a hash of relevant properties
            hash_content = {
                "role": self.role,
                "content": self.content,
                "name": self.name,
                "created_at": self.timestamp.isoformat()
            }
            if self.attributes.get("source"):
                hash_content["source"] = self.attributes["source"]
            
            # Create deterministic JSON string for hashing
            hash_str = json.dumps(hash_content, sort_keys=True)
            self.id = hashlib.sha256(hash_str.encode()).hexdigest()
            logger.debug(f"Generated message ID {self.id} from hash content: {hash_str}")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "role": "user",
                    "content": "Hello, how are you?",
                    "name": None,
                    "attributes": {}
                }
            ]
        }
    }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to a dictionary suitable for JSON serialization"""
        return {
            "id": self.id,
            "role": self.role,
            "content": self.content,
            "name": self.name,
            "attributes": self.attributes,
            "timestamp": self.timestamp.isoformat()
        } 