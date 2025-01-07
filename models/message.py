from typing import Dict, Optional, Literal, Any
from datetime import datetime
from pydantic import BaseModel, Field

class Message(BaseModel):
    """Represents a single message in a thread"""
    role: Literal["system", "user", "assistant", "function"]
    content: str
    name: Optional[str] = None
    attributes: Dict = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

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
            "role": self.role,
            "content": self.content,
            "name": self.name,
            "attributes": self.attributes,
            "timestamp": self.timestamp.isoformat()
        } 