from typing import Dict, Optional, Literal
from datetime import datetime
from pydantic import BaseModel, Field

class Message(BaseModel):
    """Represents a single message in a conversation"""
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